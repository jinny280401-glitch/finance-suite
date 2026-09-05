"""
业务编排层（Skills）

每个 Skill 文件对应一个业务场景的数据编排逻辑：
  - 决定"拉哪些维度"
  - 处理多源降级（Wind → AkShare → JQData）
  - 格式化输出

Skill 内部调用 engine/providers/ 的纯 API 适配层获取数据。
"""
