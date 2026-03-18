"""
Knowledge Updater - 知识更新管理器

管理知识库的实时更新和定时批量更新，维护知识候选池和变更日志。
"""

from typing import List, Dict, Any, Optional, Callable
from datetime import datetime, timedelta
import logging
import uuid
import hashlib

from .models import (
    UpdateMode, UpdateStatus, KnowledgeSource, CandidateStatus,
    KnowledgeCandidate, UpdateTask, ChangeLogEntry, QueryRecord
)
from .config import KnowledgeEvolutionConfig


logger = logging.getLogger(__name__)


class KnowledgeUpdater:
    """
    知识库更新管理器
    
    管理实时更新和定时批量更新两种模式，
    维护知识候选池和变更日志。
    
    Knowledge base update manager that handles real-time and batch updates,
    maintains candidate pool and change log.
    """
    
    def __init__(
        self,
        config: Optional[KnowledgeEvolutionConfig] = None,
        memory_manager: Any = None
    ):
        """
        初始化知识更新管理器
        
        Args:
            config: 知识演化配置
            memory_manager: 记忆管理器实例
        """
        self.config = config or KnowledgeEvolutionConfig.default()
        self.memory_manager = memory_manager
        
        # 候选池
        self._candidate_pool: List[KnowledgeCandidate] = []
        
        # 变更日志
        self._change_log: List[ChangeLogEntry] = []
        
        # 更新任务
        self._update_tasks: List[UpdateTask] = []
        
        # 查询日志
        self._query_log: List[QueryRecord] = []
        
        # 知识缺口记录
        self._knowledge_gaps: Dict[str, Dict[str, Any]] = {}
        
        # 统计信息
        self._stats = {
            "realtime_updates": 0,
            "batch_updates": 0,
            "rejected": 0,
            "auto_approved": 0,
            "manual_approved": 0,
            "rollbacks": 0,
        }
        
        # 回调函数
        self._on_update_callbacks: List[Callable] = []
        
        logger.info("KnowledgeUpdater initialized")
    
    # ============== 知识候选管理 ==============
    
    def add_candidate(
        self,
        content: str,
        source: KnowledgeSource,
        target_layer: str = "L1",
        metadata: Optional[Dict[str, Any]] = None
    ) -> KnowledgeCandidate:
        """
        添加知识候选条目到候选池
        
        Args:
            content: 知识内容
            source: 知识来源
            target_layer: 目标层级（L1/L2/L3）
            metadata: 元数据
            
        Returns:
            KnowledgeCandidate: 创建的候选条目
        """
        candidate = KnowledgeCandidate(
            content=content,
            source=source,
            target_layer=target_layer,
            metadata=metadata or {},
        )
        
        # 评估质量
        candidate = self.evaluate_candidate(candidate)
        
        # 检查是否自动审批
        if candidate.composite_score >= self.config.auto_approve_threshold:
            candidate.status = CandidateStatus.AUTO_APPROVED
            candidate.reviewed_at = datetime.now()
            self._stats["auto_approved"] += 1
            
            # 直接入库
            if self.config.enable_realtime_update:
                self._commit_candidate(candidate)
            else:
                self._candidate_pool.append(candidate)
        else:
            # 放入候选池等待审核
            self._candidate_pool.append(candidate)
            
            # 检查候选池容量
            if len(self._candidate_pool) > self.config.candidate_pool_max_size:
                self._cleanup_candidate_pool()
        
        logger.debug(f"Added candidate: {candidate.candidate_id}, score: {candidate.composite_score}")
        return candidate
    
    def evaluate_candidate(self, candidate: KnowledgeCandidate) -> KnowledgeCandidate:
        """
        评估知识候选条目的质量
        
        计算相关性、新颖性、可信度评分并综合评分。
        
        Args:
            candidate: 待评估的候选条目
            
        Returns:
            KnowledgeCandidate: 评估后的候选条目
        """
        # 计算相关性评分
        candidate.relevance_score = self._calculate_relevance(candidate)
        
        # 计算新颖性评分
        candidate.novelty_score = self._calculate_novelty(candidate)
        
        # 计算可信度评分
        candidate.credibility_score = self._calculate_credibility(candidate)
        
        # 综合评分（加权平均）
        candidate.composite_score = (
            self.config.relevance_weight * candidate.relevance_score +
            self.config.novelty_weight * candidate.novelty_score +
            self.config.credibility_weight * candidate.credibility_score
        )
        
        return candidate
    
    def _calculate_relevance(self, candidate: KnowledgeCandidate) -> float:
        """
        计算相关性评分
        
        基于内容与现有知识库的语义相关性。
        """
        # 简化实现：基于内容长度和结构
        content_length = len(candidate.content)
        if content_length < 10:
            return 0.2
        elif content_length < 50:
            return 0.5
        elif content_length < 200:
            return 0.7
        else:
            return 0.8
    
    def _calculate_novelty(self, candidate: KnowledgeCandidate) -> float:
        """
        计算新颖性评分
        
        基于内容与现有知识的差异度。
        """
        # 简化实现：检查是否存在相似内容
        content_hash = hashlib.md5(candidate.content.encode()).hexdigest()[:8]
        
        # 检查候选池中是否已存在
        for existing in self._candidate_pool:
            if existing.candidate_id != candidate.candidate_id:
                existing_hash = hashlib.md5(existing.content.encode()).hexdigest()[:8]
                if content_hash == existing_hash:
                    return 0.1  # 重复内容
        
        # 基于来源给予不同新颖性评分
        source_novelty = {
            KnowledgeSource.USER_QUERY: 0.7,
            KnowledgeSource.LLM_GENERATED: 0.6,
            KnowledgeSource.USER_FEEDBACK: 0.8,
            KnowledgeSource.EXTERNAL_IMPORT: 0.5,
            KnowledgeSource.GAP_FILLING: 0.9,
        }
        
        return source_novelty.get(candidate.source, 0.5)
    
    def _calculate_credibility(self, candidate: KnowledgeCandidate) -> float:
        """
        计算可信度评分
        
        基于知识来源和元数据。
        """
        base_score = 0.5
        
        # 基于来源调整
        source_credibility = {
            KnowledgeSource.USER_QUERY: 0.6,
            KnowledgeSource.LLM_GENERATED: 0.7,
            KnowledgeSource.USER_FEEDBACK: 0.8,
            KnowledgeSource.EXTERNAL_IMPORT: 0.5,
            KnowledgeSource.GAP_FILLING: 0.6,
        }
        base_score = source_credibility.get(candidate.source, 0.5)
        
        # 基于元数据调整
        if candidate.metadata.get("verified", False):
            base_score += 0.2
        if candidate.metadata.get("confidence", 0) > 0.8:
            base_score += 0.1
        
        return min(base_score, 1.0)
    
    def approve_candidate(self, candidate_id: str) -> bool:
        """
        批准候选条目入库
        
        Args:
            candidate_id: 候选条目 ID
            
        Returns:
            bool: 是否成功
        """
        for candidate in self._candidate_pool:
            if candidate.candidate_id == candidate_id and candidate.is_pending:
                candidate.status = CandidateStatus.APPROVED
                candidate.reviewed_at = datetime.now()
                self._stats["manual_approved"] += 1
                
                # 入库
                self._commit_candidate(candidate)
                
                # 从候选池移除
                self._candidate_pool.remove(candidate)
                
                logger.info(f"Approved candidate: {candidate_id}")
                return True
        
        return False
    
    def reject_candidate(self, candidate_id: str, reason: str = "") -> bool:
        """
        拒绝候选条目
        
        Args:
            candidate_id: 候选条目 ID
            reason: 拒绝原因
            
        Returns:
            bool: 是否成功
        """
        for candidate in self._candidate_pool:
            if candidate.candidate_id == candidate_id and candidate.is_pending:
                candidate.status = CandidateStatus.REJECTED
                candidate.reviewed_at = datetime.now()
                candidate.metadata["rejection_reason"] = reason
                self._stats["rejected"] += 1
                
                # 从候选池移除
                self._candidate_pool.remove(candidate)
                
                logger.info(f"Rejected candidate: {candidate_id}")
                return True
        
        return False
    
    def get_pending_candidates(self, limit: int = 100) -> List[KnowledgeCandidate]:
        """
        获取待审核的候选条目
        
        Args:
            limit: 返回数量限制
            
        Returns:
            List[KnowledgeCandidate]: 待审核候选列表
        """
        pending = [c for c in self._candidate_pool if c.is_pending]
        # 按综合评分降序排序
        pending.sort(key=lambda x: x.composite_score, reverse=True)
        return pending[:limit]
    
    def _commit_candidate(self, candidate: KnowledgeCandidate) -> Optional[str]:
        """
        将候选条目提交到知识库
        
        Args:
            candidate: 候选条目
            
        Returns:
            Optional[str]: 新记忆的 ID
        """
        if self.memory_manager is None:
            logger.warning("No memory manager configured, skipping commit")
            return None
        
        # 记录变更
        if self.config.enable_change_log:
            log_entry = ChangeLogEntry(
                operation="insert",
                layer=candidate.target_layer,
                item_id=candidate.candidate_id,
                content_summary=candidate.content[:100],
                metadata={
                    "source": candidate.source.value,
                    "composite_score": candidate.composite_score,
                }
            )
            self._add_change_log(log_entry)
        
        self._stats["realtime_updates"] += 1
        
        # 触发回调
        for callback in self._on_update_callbacks:
            try:
                callback("insert", candidate)
            except Exception as e:
                logger.error(f"Update callback error: {e}")
        
        logger.info(f"Committed candidate: {candidate.candidate_id}")
        return candidate.candidate_id
    
    def _cleanup_candidate_pool(self):
        """清理候选池，移除低分条目"""
        # 保留高分条目
        pending = [c for c in self._candidate_pool if c.is_pending]
        pending.sort(key=lambda x: x.composite_score, reverse=True)
        
        # 保留前 80% 容量
        max_keep = int(self.config.candidate_pool_max_size * 0.8)
        to_remove = pending[max_keep:]
        
        for candidate in to_remove:
            candidate.status = CandidateStatus.REJECTED
            candidate.metadata["rejection_reason"] = "pool_overflow"
            self._candidate_pool.remove(candidate)
            self._stats["rejected"] += 1
        
        logger.info(f"Cleaned up candidate pool, removed {len(to_remove)} candidates")
    
    # ============== 实时更新 ==============
    
    def realtime_update(
        self,
        content: str,
        source: KnowledgeSource,
        target_layer: str = "L1",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        实时更新知识到指定层
        
        Args:
            content: 知识内容
            source: 知识来源
            target_layer: 目标层级
            metadata: 元数据
            
        Returns:
            Optional[str]: 新记忆的 ID，如果未通过质量检查则返回 None
        """
        if not self.config.enable_realtime_update:
            logger.debug("Realtime update disabled, adding to candidate pool")
            candidate = self.add_candidate(content, source, target_layer, metadata)
            return candidate.candidate_id if candidate.status == CandidateStatus.AUTO_APPROVED else None
        
        # 创建候选并评估
        candidate = KnowledgeCandidate(
            content=content,
            source=source,
            target_layer=target_layer,
            metadata=metadata or {},
        )
        candidate = self.evaluate_candidate(candidate)
        
        # 质量检查
        if candidate.composite_score < self.config.realtime_quality_threshold:
            logger.debug(f"Realtime update rejected: score {candidate.composite_score} < {self.config.realtime_quality_threshold}")
            self._candidate_pool.append(candidate)
            return None
        
        # 直接入库
        candidate.status = CandidateStatus.AUTO_APPROVED
        candidate.reviewed_at = datetime.now()
        return self._commit_candidate(candidate)
    
    # ============== 定时批量更新 ==============
    
    def create_batch_update_task(
        self,
        description: str = "Batch update",
        target_layers: Optional[List[str]] = None
    ) -> UpdateTask:
        """
        创建批量更新任务
        
        Args:
            description: 任务描述
            target_layers: 目标层级列表
            
        Returns:
            UpdateTask: 创建的更新任务
        """
        task = UpdateTask(
            mode=UpdateMode.SCHEDULED_BATCH,
            description=description,
            target_layers=target_layers or ["L1", "L2", "L3"],
        )
        
        # 计算待处理条目数
        approved_candidates = [
            c for c in self._candidate_pool
            if c.status in (CandidateStatus.APPROVED, CandidateStatus.AUTO_APPROVED)
        ]
        task.items_total = len(approved_candidates)
        
        self._update_tasks.append(task)
        logger.info(f"Created batch update task: {task.task_id}")
        return task
    
    def execute_batch_update(self, task_id: str) -> UpdateTask:
        """
        执行批量更新任务
        
        处理候选池中已批准的条目，进行向量索引优化和图谱关系维护。
        
        Args:
            task_id: 任务 ID
            
        Returns:
            UpdateTask: 更新后的任务状态
        """
        task = self._get_task(task_id)
        if task is None:
            raise ValueError(f"Task not found: {task_id}")
        
        if task.status != UpdateStatus.PENDING:
            raise ValueError(f"Task is not pending: {task.status}")
        
        # 开始任务
        task.status = UpdateStatus.IN_PROGRESS
        task.started_at = datetime.now()
        
        try:
            # 获取已批准的候选
            approved = [
                c for c in self._candidate_pool
                if c.status in (CandidateStatus.APPROVED, CandidateStatus.AUTO_APPROVED)
            ]
            
            task.items_total = len(approved)
            
            for candidate in approved:
                try:
                    self._commit_candidate(candidate)
                    self._candidate_pool.remove(candidate)
                    task.items_processed += 1
                except Exception as e:
                    task.items_failed += 1
                    logger.error(f"Failed to commit candidate {candidate.candidate_id}: {e}")
            
            task.status = UpdateStatus.COMPLETED
            task.completed_at = datetime.now()
            self._stats["batch_updates"] += 1
            
            logger.info(f"Batch update completed: {task.items_processed}/{task.items_total}")
            
        except Exception as e:
            task.status = UpdateStatus.FAILED
            task.error_message = str(e)
            task.completed_at = datetime.now()
            logger.error(f"Batch update failed: {e}")
        
        return task
    
    # ============== 增量更新 ==============
    
    def incremental_update_l2(
        self,
        items: List[Dict[str, Any]]
    ) -> int:
        """
        增量更新 L2 语义向量
        
        Args:
            items: 待更新条目列表，每个条目包含 content, vector, metadata
            
        Returns:
            int: 成功更新的数量
        """
        updated = 0
        for item in items:
            try:
                candidate = KnowledgeCandidate(
                    content=item.get("content", ""),
                    source=KnowledgeSource.EXTERNAL_IMPORT,
                    target_layer="L2",
                    metadata=item.get("metadata", {}),
                )
                candidate = self.evaluate_candidate(candidate)
                
                if candidate.composite_score >= self.config.realtime_quality_threshold:
                    self._commit_candidate(candidate)
                    updated += 1
            except Exception as e:
                logger.error(f"Failed to update L2 item: {e}")
        
        return updated
    
    def incremental_update_l3(
        self,
        entities: List[Dict[str, Any]],
        relations: List[Dict[str, Any]]
    ) -> int:
        """
        增量更新 L3 情景图谱
        
        Args:
            entities: 实体列表
            relations: 关系列表
            
        Returns:
            int: 成功更新的数量
        """
        updated = 0
        
        # 更新实体
        for entity in entities:
            try:
                if self.config.enable_change_log:
                    log_entry = ChangeLogEntry(
                        operation="insert",
                        layer="L3",
                        item_id=entity.get("entity_id", str(uuid.uuid4())),
                        content_summary=f"Entity: {entity.get('name', 'unknown')}",
                        metadata={"type": "entity", **entity}
                    )
                    self._add_change_log(log_entry)
                updated += 1
            except Exception as e:
                logger.error(f"Failed to update L3 entity: {e}")
        
        # 更新关系
        for relation in relations:
            try:
                if self.config.enable_change_log:
                    log_entry = ChangeLogEntry(
                        operation="insert",
                        layer="L3",
                        item_id=relation.get("relation_id", str(uuid.uuid4())),
                        content_summary=f"Relation: {relation.get('relation_type', 'unknown')}",
                        metadata={"type": "relation", **relation}
                    )
                    self._add_change_log(log_entry)
                updated += 1
            except Exception as e:
                logger.error(f"Failed to update L3 relation: {e}")
        
        return updated
    
    # ============== 变更日志 ==============
    
    def _add_change_log(self, entry: ChangeLogEntry):
        """添加变更日志条目"""
        self._change_log.append(entry)
        
        # 限制日志大小
        if len(self._change_log) > self.config.change_log_max_entries:
            self._change_log = self._change_log[-self.config.change_log_max_entries:]
    
    def get_change_log(
        self,
        limit: int = 100,
        layer: Optional[str] = None,
        operation: Optional[str] = None
    ) -> List[ChangeLogEntry]:
        """
        获取变更日志
        
        Args:
            limit: 返回数量限制
            layer: 按层级过滤
            operation: 按操作类型过滤
            
        Returns:
            List[ChangeLogEntry]: 变更日志列表
        """
        logs = self._change_log.copy()
        
        if layer:
            logs = [l for l in logs if l.layer == layer]
        if operation:
            logs = [l for l in logs if l.operation == operation]
        
        # 按时间降序
        logs.sort(key=lambda x: x.timestamp, reverse=True)
        return logs[:limit]
    
    def rollback(self, log_id: str) -> bool:
        """
        根据变更日志回滚操作
        
        Args:
            log_id: 变更日志 ID
            
        Returns:
            bool: 是否成功
        """
        if not self.config.enable_rollback:
            logger.warning("Rollback is disabled")
            return False
        
        log_entry = None
        for entry in self._change_log:
            if entry.log_id == log_id:
                log_entry = entry
                break
        
        if log_entry is None:
            logger.warning(f"Change log not found: {log_id}")
            return False
        
        if log_entry.rollback_executed:
            logger.warning(f"Rollback already executed: {log_id}")
            return False
        
        # 检查回滚窗口
        age_hours = (datetime.now() - log_entry.timestamp).total_seconds() / 3600
        if age_hours > self.config.rollback_window_hours:
            logger.warning(f"Rollback window exceeded: {age_hours} hours")
            return False
        
        # 执行回滚
        try:
            if log_entry.operation == "insert":
                # 回滚插入 = 删除
                # TODO: 调用 memory_manager 删除
                pass
            elif log_entry.operation == "update":
                # 回滚更新 = 恢复旧值
                # TODO: 使用 previous_content 恢复
                pass
            elif log_entry.operation == "delete":
                # 回滚删除 = 重新插入
                # TODO: 使用 previous_content 重新插入
                pass
            
            log_entry.rollback_executed = True
            self._stats["rollbacks"] += 1
            
            # 记录回滚操作
            rollback_log = ChangeLogEntry(
                operation="rollback",
                layer=log_entry.layer,
                item_id=log_entry.item_id,
                content_summary=f"Rollback of {log_entry.operation}",
                metadata={"original_log_id": log_id}
            )
            self._add_change_log(rollback_log)
            
            logger.info(f"Rollback executed: {log_id}")
            return True
            
        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            return False
    
    # ============== 查询驱动知识积累 ==============
    
    def on_query_completed(
        self,
        query: str,
        answer: str,
        evidence: List[str],
        hit: bool,
        confidence: float = 0.0,
        latency_ms: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        查询完成后的回调，用于积累知识
        
        Args:
            query: 查询文本
            answer: 回答内容
            evidence: 证据列表
            hit: 是否命中知识库
            confidence: 回答置信度
            latency_ms: 响应延迟（毫秒）
            metadata: 额外元数据
        """
        if not self.config.enable_query_driven_accumulation:
            return
        
        # 记录查询
        record = QueryRecord(
            query=query,
            answer=answer,
            evidence=evidence,
            hit=hit,
            confidence=confidence,
            latency_ms=latency_ms,
            metadata=metadata or {},
        )
        
        if self.config.enable_query_logging:
            self._query_log.append(record)
            if len(self._query_log) > self.config.query_log_max_entries:
                self._query_log = self._query_log[-self.config.query_log_max_entries:]
        
        # 如果未命中，记录知识缺口
        if not hit and self.config.gap_detection_enabled:
            self._record_knowledge_gap(query, metadata)
        
        # 如果答案质量高，考虑加入候选池
        if self.config.accumulate_high_quality_answers:
            if confidence >= self.config.min_answer_confidence and len(evidence) > 0:
                # 将高质量回答加入候选池
                combined_content = f"Q: {query}\nA: {answer}"
                self.add_candidate(
                    content=combined_content,
                    source=KnowledgeSource.LLM_GENERATED,
                    target_layer="L2",
                    metadata={
                        "original_query": query,
                        "confidence": confidence,
                        "evidence_count": len(evidence),
                    }
                )
    
    def _record_knowledge_gap(self, query: str, metadata: Optional[Dict[str, Any]] = None):
        """记录知识缺口"""
        # 使用查询的简化形式作为 key
        gap_key = hashlib.md5(query.lower().encode()).hexdigest()[:12]
        
        if gap_key in self._knowledge_gaps:
            self._knowledge_gaps[gap_key]["frequency"] += 1
            self._knowledge_gaps[gap_key]["last_seen"] = datetime.now()
        else:
            self._knowledge_gaps[gap_key] = {
                "query": query,
                "frequency": 1,
                "first_seen": datetime.now(),
                "last_seen": datetime.now(),
                "metadata": metadata or {},
            }
        
        logger.debug(f"Recorded knowledge gap: {query[:50]}...")
    
    def get_knowledge_gaps(self, min_frequency: int = 2) -> List[Dict[str, Any]]:
        """
        获取知识缺口列表
        
        Args:
            min_frequency: 最小出现频率
            
        Returns:
            List[Dict]: 知识缺口列表
        """
        gaps = [
            {"gap_key": k, **v}
            for k, v in self._knowledge_gaps.items()
            if v["frequency"] >= min_frequency
        ]
        gaps.sort(key=lambda x: x["frequency"], reverse=True)
        return gaps
    
    # ============== 统计与工具 ==============
    
    def get_update_stats(self) -> Dict[str, Any]:
        """
        获取更新统计信息
        
        Returns:
            Dict: 统计信息
        """
        return {
            **self._stats,
            "candidate_pool_size": len(self._candidate_pool),
            "pending_candidates": len([c for c in self._candidate_pool if c.is_pending]),
            "change_log_size": len(self._change_log),
            "query_log_size": len(self._query_log),
            "knowledge_gaps_count": len(self._knowledge_gaps),
            "active_tasks": len([t for t in self._update_tasks if t.status == UpdateStatus.IN_PROGRESS]),
        }
    
    def _get_task(self, task_id: str) -> Optional[UpdateTask]:
        """获取任务"""
        for task in self._update_tasks:
            if task.task_id == task_id:
                return task
        return None
    
    def get_tasks(
        self,
        status: Optional[UpdateStatus] = None,
        limit: int = 50
    ) -> List[UpdateTask]:
        """
        获取任务列表
        
        Args:
            status: 按状态过滤
            limit: 返回数量限制
            
        Returns:
            List[UpdateTask]: 任务列表
        """
        tasks = self._update_tasks.copy()
        
        if status:
            tasks = [t for t in tasks if t.status == status]
        
        # 按创建时间降序
        tasks.sort(key=lambda x: x.task_id, reverse=True)
        return tasks[:limit]
    
    def register_update_callback(self, callback: Callable):
        """
        注册更新回调函数
        
        Args:
            callback: 回调函数，接收 (operation, candidate) 参数
        """
        self._on_update_callbacks.append(callback)
    
    def clear_stats(self):
        """清空统计信息"""
        self._stats = {
            "realtime_updates": 0,
            "batch_updates": 0,
            "rejected": 0,
            "auto_approved": 0,
            "manual_approved": 0,
            "rollbacks": 0,
        }
