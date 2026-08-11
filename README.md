# Make Pindou Pattern

把人物照片或已经确认的卡通图，转换成可制作、可打印、可分享的 MARD 拼豆图纸。

这个 Skill 把工作拆成两步：先让 GPT、Gemini 或其他图像模型生成好看的卡通母图，再用确定性脚本完成色号映射、连通性检查和图纸导出。这样既保留人物五官与表情，也避免让图像模型直接绘制容易出错的网格、色号和颗数。

## 主要特点

- 默认输出 `chart.png` 和 `chart.pdf`，适合手机分享与打印。
- 使用 221 色 MARD 屏幕参考色表，图纸内显示 A2、A3、F17 等色号。
- 检查头像组合是否连成一体，并识别容易断裂的细连接点。
- 清理绿色皮肤斑点和孤立噪点，同时优先保护脸、眼睛、眉毛、嘴和眼镜。
- 普通模式不输出 SVG、CSV 或调试报告，保持交付目录干净。

## 在 Codex 中使用

把仓库安装为 Skill 后，可以这样描述任务：

```text
Use $make-pindou-pattern to turn this group photo into a cute connected MARD bead pattern.
```

如果已经有满意的卡通图，也可以直接运行转换器：

```bash
scripts/pindou cartoon.png --output-dir output --grid 72 --colors 22 --max-beads 3400
```

运行环境需要 Python 3 和 Pillow；安装 ReportLab 后会优先生成矢量 PDF，否则会生成高分辨率图片 PDF。

## 输出

- `chart.png`：高清带网格、MARD 色号和用量统计的图片
- `chart.pdf`：单页打印版图纸

`--debug-exports` 仅用于诊断，会额外输出 SVG、CSV、JSON 和质量报告。

## 验证

```bash
python3 scripts/smoke_test.py
```

它会生成四人连体测试图，并检查输出格式、豆子上限、连通性和挂坠安全性。

## 生成字节 AgentBuddy 上传包

```bash
python3 scripts/package_platform.py --version 1.0.0
```

生成的 ZIP 以 `SKILL.md` 为根目录标识，并同时包含转换脚本和色号参考文件，适用于 AgentBuddy 的“本地文件上传”。通过代码仓库自动导入时，仓库本身就是 `make-pindou-pattern` 这个 Skill 目录。

## 说明

MARD 色号与 HEX 值为屏幕参考，显示器、批次和实物颜色可能存在差异。项目与 MARD 品牌无隶属或官方合作关系。

## License

[MIT](LICENSE)
