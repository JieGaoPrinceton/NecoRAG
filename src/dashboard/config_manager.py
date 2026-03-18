"""
配置管理器
管理 RAG Profile 的存储、加载和应用
"""

from typing import Dict, List, Optional, Any
from pathlib import Path
import json
from datetime import datetime
import uuid
from src.dashboard.models import RAGProfile, ModuleConfig


class ConfigManager:
    """
    配置管理器
    
    功能：
    - 保存/加载配置 Profile
    - 切换活动 Profile
    - 导入/导出配置
    - 参数验证
    """
    
    def __init__(self, config_dir: str = "./configs"):
        """
        初始化配置管理器
        
        Args:
            config_dir: 配置文件存储目录
        """
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # 配置缓存
        self._profiles: Dict[str, RAGProfile] = {}
        self._active_profile_id: Optional[str] = None
        
        # 加载所有配置
        self._load_all_profiles()
    
    def create_profile(
        self,
        profile_name: str,
        description: str = "",
        set_active: bool = False
    ) -> RAGProfile:
        """
        创建新的配置 Profile
        
        Args:
            profile_name: Profile 名称
            description: 描述
            set_active: 是否设为活动
            
        Returns:
            RAGProfile: 创建的 Profile
        """
        profile = RAGProfile(
            profile_id=str(uuid.uuid4()),
            profile_name=profile_name,
            description=description,
            is_active=set_active
        )
        
        # 保存
        self._profiles[profile.profile_id] = profile
        self._save_profile(profile)
        
        # 设为活动
        if set_active:
            self.set_active_profile(profile.profile_id)
        
        return profile
    
    def get_profile(self, profile_id: str) -> Optional[RAGProfile]:
        """
        获取 Profile
        
        Args:
            profile_id: Profile ID
            
        Returns:
            Optional[RAGProfile]: Profile 对象
        """
        return self._profiles.get(profile_id)
    
    def get_all_profiles(self) -> List[RAGProfile]:
        """
        获取所有 Profile
        
        Returns:
            List[RAGProfile]: Profile 列表
        """
        return list(self._profiles.values())
    
    def get_active_profile(self) -> Optional[RAGProfile]:
        """
        获取当前活动的 Profile
        
        Returns:
            Optional[RAGProfile]: 活动 Profile
        """
        if self._active_profile_id:
            return self._profiles.get(self._active_profile_id)
        return None
    
    def set_active_profile(self, profile_id: str) -> bool:
        """
        设置活动 Profile
        
        Args:
            profile_id: Profile ID
            
        Returns:
            bool: 是否成功
        """
        if profile_id not in self._profiles:
            return False
        
        # 取消之前的活动状态
        for profile in self._profiles.values():
            profile.is_active = False
        
        # 设置新的活动状态
        profile = self._profiles[profile_id]
        profile.is_active = True
        profile.updated_at = datetime.now()
        
        self._active_profile_id = profile_id
        self._save_profile(profile)
        
        return True
    
    def update_profile(self, profile_id: str, updates: Dict[str, Any]) -> bool:
        """
        更新 Profile
        
        Args:
            profile_id: Profile ID
            updates: 更新内容
            
        Returns:
            bool: 是否成功
        """
        profile = self._profiles.get(profile_id)
        if not profile:
            return False
        
        # 更新基本信息
        if 'profile_name' in updates:
            profile.profile_name = updates['profile_name']
        if 'description' in updates:
            profile.description = updates['description']
        
        # 更新模块配置
        for module in ['whiskers', 'memory', 'retrieval', 'grooming', 'purr']:
            config_key = f'{module}_config'
            if config_key in updates:
                module_config = getattr(profile, config_key)
                module_config.parameters.update(updates[config_key])
        
        profile.updated_at = datetime.now()
        self._save_profile(profile)
        
        return True
    
    def delete_profile(self, profile_id: str) -> bool:
        """
        删除 Profile
        
        Args:
            profile_id: Profile ID
            
        Returns:
            bool: 是否成功
        """
        if profile_id not in self._profiles:
            return False
        
        # 删除文件
        profile_file = self.config_dir / f"{profile_id}.json"
        if profile_file.exists():
            profile_file.delete()
        
        # 从缓存移除
        del self._profiles[profile_id]
        
        # 如果删除的是活动 Profile，清除活动状态
        if self._active_profile_id == profile_id:
            self._active_profile_id = None
        
        return True
    
    def duplicate_profile(self, profile_id: str, new_name: str) -> Optional[RAGProfile]:
        """
        复制 Profile
        
        Args:
            profile_id: 源 Profile ID
            new_name: 新名称
            
        Returns:
            Optional[RAGProfile]: 新 Profile
        """
        source = self._profiles.get(profile_id)
        if not source:
            return None
        
        # 创建新 Profile
        new_profile = RAGProfile(
            profile_id=str(uuid.uuid4()),
            profile_name=new_name,
            description=f"复制自: {source.profile_name}",
        )
        
        # 复制配置
        new_profile.whiskers_config.parameters = source.whiskers_config.parameters.copy()
        new_profile.memory_config.parameters = source.memory_config.parameters.copy()
        new_profile.retrieval_config.parameters = source.retrieval_config.parameters.copy()
        new_profile.grooming_config.parameters = source.grooming_config.parameters.copy()
        new_profile.purr_config.parameters = source.purr_config.parameters.copy()
        
        # 保存
        self._profiles[new_profile.profile_id] = new_profile
        self._save_profile(new_profile)
        
        return new_profile
    
    def export_profile(self, profile_id: str, export_path: str) -> bool:
        """
        导出 Profile 到文件
        
        Args:
            profile_id: Profile ID
            export_path: 导出路径
            
        Returns:
            bool: 是否成功
        """
        profile = self._profiles.get(profile_id)
        if not profile:
            return False
        
        try:
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(profile.to_dict(), f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"导出失败: {e}")
            return False
    
    def import_profile(self, import_path: str) -> Optional[RAGProfile]:
        """
        从文件导入 Profile
        
        Args:
            import_path: 导入路径
            
        Returns:
            Optional[RAGProfile]: 导入的 Profile
        """
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            profile = RAGProfile.from_dict(data)
            profile.profile_id = str(uuid.uuid4())  # 生成新 ID
            profile.is_active = False
            
            self._profiles[profile.profile_id] = profile
            self._save_profile(profile)
            
            return profile
        except Exception as e:
            print(f"导入失败: {e}")
            return None
    
    def _save_profile(self, profile: RAGProfile) -> None:
        """
        保存 Profile 到文件
        
        Args:
            profile: Profile 对象
        """
        profile_file = self.config_dir / f"{profile.profile_id}.json"
        with open(profile_file, 'w', encoding='utf-8') as f:
            json.dump(profile.to_dict(), f, indent=2, ensure_ascii=False)
    
    def _load_all_profiles(self) -> None:
        """
        加载所有 Profile
        """
        for profile_file in self.config_dir.glob("*.json"):
            try:
                with open(profile_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                profile = RAGProfile.from_dict(data)
                self._profiles[profile.profile_id] = profile
                
                # 记录活动 Profile
                if profile.is_active:
                    self._active_profile_id = profile.profile_id
            except Exception as e:
                print(f"加载配置失败 {profile_file}: {e}")
        
        # 如果没有配置，创建默认配置
        if not self._profiles:
            self.create_profile(
                profile_name="默认配置",
                description="NecoRAG 默认配置",
                set_active=True
            )
