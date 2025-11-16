# ESP32 8通道风扇控制器

基于ESP32和MicroPython的8通道风扇控制系统，支持PWM调速和FG反馈信号转速测量。

## 功能特性

- ✅ 支持8路独立风扇PWM控制
- ✅ **FG信号频率测量和转速计算**
- ✅ **实时转速监测 (RPM)**
- ✅ 风扇状态实时监测
- ✅ 紧急停止功能
- ✅ 渐进式调速控制
- ✅ 状态LED指示
- ✅ 交互式控制界面
- ✅ 完整的错误处理
- ✅ **中断驱动的FG信号处理**

## 硬件要求

### ESP32开发板
- 任何支持MicroPython的ESP32开发板
- 建议使用具有足够GPIO引脚的型号

### 风扇连接
- **PWM控制线**: 连接到ESP32的GPIO引脚 (4线风扇)
- **FG反馈信号线**: 连接到ESP32的GPIO引脚 (测量转速)
- **电源**: 根据风扇规格提供适当电源
- **地线**: 共地连接

### FG信号说明
- FG (Frequency Generator) 信号是风扇输出的脉冲频率信号
- 信号频率与风扇转速成正比
- 通常每转产生2个脉冲 (可配置)
- 支持3线和4线风扇的FG信号测量

## 引脚分配

### 风扇控制引脚 (PWM输出)
- 风扇1: GPIO32
- 风扇2: GPIO33
- 风扇3: GPIO25
- 风扇4: GPIO26
- 风扇5: GPIO27
- 风扇6: GPIO14
- 风扇7: GPIO12
- 风扇8: GPIO13

### 风扇FG反馈引脚 (脉冲输入)
- 风扇1: GPIO19
- 风扇2: GPIO18
- 风扇3: GPIO5
- 风扇4: GPIO17
- 风扇5: GPIO16
- 风扇6: GPIO4
- 风扇7: GPIO2
- 风扇8: GPIO15

**注意**: FG引脚使用中断模式，支持上升沿和下降沿触发，能够精确测量脉冲频率。

### 系统指示
- 状态LED: GPIO2 (ESP32内置LED)

## 安装和使用

### 1. 准备工作
```bash
# 确保ESP32已刷入MicroPython固件
# 使用ampy或其他工具上传文件到ESP32
```

### 2. 上传文件
```bash
# 上传所有Python文件到ESP32
ampy put fan_controller.py
ampy put main.py
ampy put config.py
ampy put test_fans.py
```

### 3. 运行程序

#### 简单测试
```python
# 在REPL中运行
import test_fans
test_fans.simple_test()
```

#### 完整演示
```python
# 在REPL中运行
import main
main.main()
```

## 使用方法

### 基本控制
```python
from fan_controller import FanController

# 创建控制器实例
controller = FanController()

# 设置单个风扇转速 (0-100%)
controller.set_fan_speed(0, 75)  # 风扇1设置75%转速

# 设置所有风扇转速
controller.set_all_fans_speed(50)  # 所有风扇50%转速

# 停止风扇
controller.stop_fan(0)  # 停止风扇1
controller.stop_all_fans()  # 停止所有风扇

# 紧急停止
controller.emergency_stop()
```

### FG信号和转速监测
```python
# 读取FG信号频率
fg_freq = controller.read_fan_fg_frequency(0)
print(f"风扇1 FG频率: {fg_freq}Hz")

# 读取风扇转速 (RPM)
rpm = controller.read_fan_rpm(0)
print(f"风扇1转速: {rpm}RPM")

# 读取所有风扇转速
all_rpm = controller.read_all_fans_rpm()
for fan_id, rpm in all_rpm.items():
    print(f"风扇{fan_id+1}: {rpm}RPM")

# 读取风扇状态 (基于转速阈值)
status = controller.read_fan_feedback(0, threshold_rpm=500)
print(f"风扇1状态: {'正常' if status else '异常'}")

# 获取详细状态报告
controller.get_status_report(detailed=True)
```

### 等待转速稳定
```python
# 等待风扇转速稳定到目标值
success = controller.wait_for_rpm_stabilization(
    fan_id=0,
    target_rpm=2000,
    timeout=10,
    tolerance=50
)
print(f"转速稳定: {'成功' if success else '超时'}")
```

## 交互式命令

在交互式模式下，可以使用以下命令：

- `fan <编号> <转速>` - 控制单个风扇
  - 例如: `fan 3 60` (风扇3设置60%转速)
- `all <转速>` - 控制所有风扇
  - 例如: `all 40` (所有风扇40%转速)
- `stop` - 停止所有风扇
- `status` - 查看基本状态报告
- `detail` - 查看详细状态报告 (包含FG频率和RPM)
- `rpm <编号>` - 查看指定风扇转速
  - 例如: `rpm 2` (查看风扇2转速)
- `fg <编号>` - 查看指定风扇FG频率
  - 例如: `fg 2` (查看风扇2 FG频率)
- `allrpm` - 查看所有风扇转速
- `test` - 运行功能测试
- `quit` - 退出程序

## 配置修改

可以通过修改 `config.py` 文件来自定义系统配置：

```python
# 修改引脚分配
FAN_CONTROL_PINS = [32, 33, 25, 26, 27, 14, 12, 13]
FAN_FEEDBACK_PINS = [19, 18, 5, 17, 16, 4, 2, 15]

# 修改PWM频率
PWM_FREQUENCY = 25000  # 25kHz

# 修改系统参数
SYSTEM_CONFIG = {
    "fan_count": 8,
    "default_speed": 50,
    "max_speed": 100,
    "min_speed": 0,
}
```

## 注意事项

### 硬件连接
- 确保风扇电源与ESP32电源隔离
- 使用适当的电平转换电路（如需要）
- 检查所有接线是否正确

### 软件配置
- MicroPython版本建议1.18+
- 确保引脚没有被其他功能占用
- 根据实际硬件调整引脚配置

### 安全考虑
- 实施适当的过流保护
- 定期检查风扇运行状态
- 保留紧急停止功能

## 故障排除

### 常见问题

**风扇不转动**
- 检查电源连接和电压
- 确认PWM信号输出 (示波器检查)
- 检查风扇本身是否正常
- 确认风扇类型 (3线/4线) 和接线

**FG信号异常/读取不到转速**
- 检查FG信号线连接
- 确认风扇支持FG输出
- 检查FG信号电平 (是否需要上拉电阻)
- 验证FG引脚配置是否正确
- 使用示波器检查FG信号波形

**转速读数不准确**
- 确认每转脉冲数配置 (通常为2)
- 检查测量时间间隔
- 验证FG信号质量
- 调整转速稳定等待时间

**程序运行错误**
- 检查MicroPython版本 (建议1.18+)
- 确认所有文件已上传
- 查看错误信息并调试
- 检查GPIO引脚是否被占用

### 调试建议

1. 使用简单测试程序验证硬件连接
2. 逐个测试风扇功能
3. 监控串口输出信息
4. 使用LED状态指示辅助调试
5. **FG信号调试**:
   - 使用示波器观察FG信号波形
   - 检查信号频率是否与转速成正比
   - 验证中断计数器是否正常工作
   - 测试不同转速下的FG信号输出

## 扩展功能

系统支持以下扩展：

- 添加温度传感器联动控制
- 实现网络远程控制
- 添加数据记录功能
- 集成更多传感器类型

## 技术支持

如有问题，请检查：
1. 硬件连接是否正确
2. 软件配置是否匹配
3. MicroPython环境是否正常

---

**版本**: 1.0
**作者**: Claude
**许可**: MIT