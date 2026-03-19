#!/bin/bash
# NecoRAG 双仓库同步脚本
# 功能：同步代码到 Gitee 和 GitHub

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   NecoRAG 双仓库同步工具                           ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════╝${NC}"
echo ""

# 检查当前分支
CURRENT_BRANCH=$(git branch --show-current)
echo -e "${YELLOW}📍 当前分支:${NC} $CURRENT_BRANCH"

# 检查 Git 状态
echo -e "${YELLOW}🔍 检查 Git 状态...${NC}"
git status --short

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Git 状态检查失败${NC}"
    exit 1
fi

# 询问是否推送
echo ""
echo -e "${YELLOW}请选择同步方式:${NC}"
echo "  1) 仅推送到 Gitee (origin)"
echo "  2) 仅推送到 GitHub (github)"
echo "  3) 同时推送到两个仓库 (推荐)"
echo "  4) 只查看状态，不推送"
echo ""
read -p "请输入选项 (1/2/3/4): " choice

case $choice in
    1)
        echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "${GREEN}🚀 推送到 Gitee...${NC}"
        echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        git push origin $CURRENT_BRANCH
        
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✅ Gitee 推送成功!${NC}"
            echo -e "${BLUE}📍 仓库地址：https://gitee.com/qijie2026/NecoRAG${NC}"
        else
            echo -e "${RED}❌ Gitee 推送失败!${NC}"
            exit 1
        fi
        ;;
        
    2)
        echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "${GREEN}🚀 推送到 GitHub...${NC}"
        echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        git push github $CURRENT_BRANCH
        
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✅ GitHub 推送成功!${NC}"
            echo -e "${BLUE}📍 仓库地址：https://github.com/JieGaoPrinceton/NecoRAG${NC}"
        else
            echo -e "${RED}❌ GitHub 推送失败!${NC}"
            exit 1
        fi
        ;;
        
    3)
        echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "${GREEN}🚀 开始同步到两个仓库...${NC}"
        echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        
        # 推送到 Gitee
        echo -e "${YELLOW}[1/2] 推送到 Gitee...${NC}"
        git push origin $CURRENT_BRANCH
        
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✅ Gitee 推送成功!${NC}"
        else
            echo -e "${RED}❌ Gitee 推送失败!${NC}"
            exit 1
        fi
        
        echo ""
        
        # 推送到 GitHub
        echo -e "${YELLOW}[2/2] 推送到 GitHub...${NC}"
        git push github $CURRENT_BRANCH
        
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✅ GitHub 推送成功!${NC}"
        else
            echo -e "${RED}❌ GitHub 推送失败!${NC}"
            echo -e "${YELLOW}💡 提示：请检查 GitHub Token 配置或网络连接${NC}"
            exit 1
        fi
        
        echo ""
        echo -e "${GREEN}╔════════════════════════════════════════════════════╗${NC}"
        echo -e "${GREEN}║   ✅ 同步完成！两个仓库都已更新                    ║${NC}"
        echo -e "${GREEN}╚════════════════════════════════════════════════════╝${NC}"
        echo ""
        echo -e "${BLUE}📍 Gitee 仓库：https://gitee.com/qijie2026/NecoRAG${NC}"
        echo -e "${BLUE}📍 GitHub 仓库：https://github.com/JieGaoPrinceton/NecoRAG${NC}"
        ;;
        
    4)
        echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "${YELLOW}📊 当前状态${NC}"
        echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo ""
        echo -e "${YELLOW}远程仓库配置:${NC}"
        git remote -v | grep -E "(origin|github)" | while read line; do
            echo "  $line"
        done
        echo ""
        echo -e "${YELLOW}最近提交记录:${NC}"
        git log --oneline -5
        echo ""
        echo -e "${YELLOW}分支信息:${NC}"
        git branch -a
        ;;
        
    *)
        echo -e "${RED}❌ 无效的选项${NC}"
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}✨ 操作完成！${NC}"
