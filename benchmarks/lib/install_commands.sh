#!/usr/bin/env bash
# 一键把 benchmark/evolve 装到两个宿主（spec v2 §4.1 修 D6）：
#   - Claude Code: ~/.claude/commands/*.md
#   - ZCode:       ~/.zcode/skills/{benchmark,evolve}/SKILL.md
# 幂等；仓库内文件是单一事实源，重复执行即更新。
set -euo pipefail

SRC="$(cd "$(dirname "$0")/../.." && pwd)"   # 仓库根
for cmd in benchmark evolve; do
  mkdir -p "$HOME/.claude/commands" "$HOME/.zcode/skills/$cmd"
  cp "$SRC/.claude/commands/$cmd.md" "$HOME/.claude/commands/$cmd.md"
  cp "$SRC/.zcode/skills/$cmd/SKILL.md" "$HOME/.zcode/skills/$cmd/SKILL.md"
  echo "installed: $cmd -> ~/.claude/commands/$cmd.md, ~/.zcode/skills/$cmd/SKILL.md"
done
echo "done. 新会话生效（ZCode 需重开一次会话以注册 skill）。"
