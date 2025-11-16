"""
风扇系统配置文件
可以在这里修改引脚分配和系统参数
"""

# 风扇控制引脚配置 (GPIO编号)
FAN_CONTROL_PINS = [
    32, 33, 25, 26,  # 风扇1-4
    27, 14, 12, 13   # 风扇5-8
]

# 风扇反馈引脚配置 (GPIO编号)
FAN_FEEDBACK_PINS = [
    19, 18, 5, 17,   # 风扇1-4反馈
    16, 4, 2, 15     # 风扇5-8反馈
]

# PWM配置
PWM_FREQUENCY = 25000  # 25kHz (适合大多数风扇)
PWM_RESOLUTION = 1023  # 10位分辨率

# 系统配置
SYSTEM_CONFIG = {
    "fan_count": 8,           # 风扇数量
    "default_speed": 50,      # 默认转速百分比
    "max_speed": 100,         # 最大转速百分比
    "min_speed": 0,           # 最小转速百分比
    "emergency_stop_delay": 0.1,  # 紧急停止响应时间(秒)
    "monitor_interval": 5,    # 监控间隔(秒)
}

# 引脚模式配置
PIN_MODES = {
    "control": "PWM_OUT",     # 控制引脚模式
    "feedback": "IN_PULL_UP", # 反馈引脚模式
    "led": "OUT"              # LED引脚模式
}

# 状态LED配置
STATUS_LED_PIN = 2  # ESP32内置LED

# 风扇特性配置
FAN_CHARACTERISTICS = {
    "startup_delay": 2.0,     # 风扇启动延迟(秒)
    "stabilization_time": 3.0, # 转速稳定时间(秒)
    "min_working_speed": 20,   # 最低工作转速百分比
}

# 错误处理配置
ERROR_HANDLING = {
    "retry_count": 3,          # 重试次数
    "retry_delay": 0.5,        # 重试延迟(秒)
    "ignore_missing_fans": True, # 忽略缺失的风扇
}