# Contributing

欢迎提交可复现的问题、质量改进和新的教学场景。请不要在 Issue、PR、测试样例或截图中包含私人材料、真实凭证、Cookie、本机用户路径或未授权内容。

## 提交前

1. 保持改动聚焦于一个问题。
2. 更新或增加对应测试。
3. 运行：

```bash
python3 -m unittest discover -s tests -v
python3 -m py_compile scripts/*.py tests/*.py
```

4. Skill 元数据或结构有改动时，使用 Codex 的 `skill-creator` 校验器检查仓库根目录。
5. 不要提交生成缓存、QA 中间文件、完整受版权保护的来源、个人对话或真实密钥。

## Pull Request

说明问题、修改方式、验证结果和可能影响的输出模式。视觉或交互改动请附脱敏后的前后对比截图。

---

Reproducible fixes, quality improvements, and new teaching scenarios are welcome. Never include private sources, real credentials, cookies, local user paths, personal conversations, or unauthorized material in issues, pull requests, fixtures, or screenshots.
