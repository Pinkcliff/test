"""
ESP32 8通道风扇控制器
支持PWM调速和FG反馈信号读取
作者: Claude
"""

from machine import Pin, PWM
import time
import micropython

class FanController:
    def __init__(self):
        # 风扇控制引脚 (PWM输出)
        self.fan_pins = [
            32, 33, 25, 26, 27, 14, 12, 13  # ESP32的GPIO引脚
        ]

        # 风扇FG反馈引脚 (脉冲输入)
        self.fg_pins = [
            19, 18, 5, 17, 16, 4, 2, 15  # ESP32的GPIO引脚
        ]

        # 初始化PWM控制
        self.fan_pwms = []
        for i, pin in enumerate(self.fan_pins):
            try:
                pwm = PWM(Pin(pin), freq=25000, duty=0)  # 25kHz PWM频率
                self.fan_pwms.append(pwm)
                print(f"风扇 {i+1} 控制引脚初始化成功: GPIO{pin}")
            except Exception as e:
                print(f"风扇 {i+1} 控制引脚初始化失败: {e}")
                self.fan_pwms.append(None)

        # FG信号相关变量
        self.fg_counters = [0] * 8  # 脉冲计数器
        self.fg_last_time = [0] * 8  # 上次测量时间
        self.fg_frequencies = [0] * 8  # 当前频率
        self.fg_pins_list = []  # FG引脚对象列表
        self.fan_count = len(self.fan_pins)

        # 初始化FG引脚和中断
        self._init_fg_interrupts()

        print(f"风扇控制器初始化完成，共 {self.fan_count} 个通道")

    def _init_fg_interrupts(self):
        """初始化FG信号中断处理"""
        # 为每个风扇创建中断处理函数
        for i in range(self.fan_count):
            try:
                fg_pin = Pin(self.fg_pins[i], Pin.IN, Pin.PULL_UP)
                self.fg_pins_list.append(fg_pin)

                # 创建专用的中断处理函数
                def make_handler(fan_id):
                    def handler(pin):
                        self.fg_counters[fan_id] += 1
                    return handler

                # 设置中断，触发两个边沿以捕获完整脉冲
                fg_pin.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING,
                          handler=make_handler(i))
                print(f"风扇 {i+1} FG引脚初始化成功: GPIO{self.fg_pins[i]}")

            except Exception as e:
                print(f"风扇 {i+1} FG引脚初始化失败: {e}")
                self.fg_pins_list.append(None)

    def _measure_frequency(self, fan_id):
        """测量指定风扇的FG信号频率"""
        if not (0 <= fan_id < self.fan_count):
            return 0

        current_time = time.ticks_ms()

        # 如果上次测量时间存在，计算频率
        if self.fg_last_time[fan_id] > 0:
            time_diff = time.ticks_diff(current_time, self.fg_last_time[fan_id])

            if time_diff > 0:
                # 计算频率 (Hz)
                pulse_count = self.fg_counters[fan_id]
                # 每个完整脉冲产生2次中断（上升沿+下降沿）
                full_pulses = pulse_count / 2
                self.fg_frequencies[fan_id] = (full_pulses * 1000) / time_diff
            else:
                self.fg_frequencies[fan_id] = 0
        else:
            self.fg_frequencies[fan_id] = 0

        # 重置计数器和时间
        self.fg_counters[fan_id] = 0
        self.fg_last_time[fan_id] = current_time

        return self.fg_frequencies[fan_id]

    def set_fan_speed(self, fan_id, speed):
        """
        设置风扇转速
        fan_id: 风扇编号 (0-7)
        speed: 转速百分比 (0-100)
        """
        if not (0 <= fan_id < self.fan_count):
            print(f"错误: 风扇编号 {fan_id} 超出范围")
            return False

        if not (0 <= speed <= 100):
            print(f"错误: 转速 {speed} 超出范围 (0-100)")
            return False

        if self.fan_pwms[fan_id] is None:
            print(f"错误: 风扇 {fan_id+1} 未初始化")
            return False

        # 将百分比转换为PWM占空比 (0-1023)
        duty = int(speed * 1023 / 100)
        self.fan_pwms[fan_id].duty(duty)
        print(f"风扇 {fan_id+1} 转速设置为: {speed}% (PWM: {duty})")
        return True

    def set_all_fans_speed(self, speed):
        """
        设置所有风扇转速
        speed: 转速百分比 (0-100)
        """
        success_count = 0
        for i in range(self.fan_count):
            if self.set_fan_speed(i, speed):
                success_count += 1

        print(f"共设置 {success_count}/{self.fan_count} 个风扇")
        return success_count == self.fan_count

    def read_fan_fg_frequency(self, fan_id):
        """
        读取风扇FG信号频率
        fan_id: 风扇编号 (0-7)
        返回: FG信号频率 (Hz)
        """
        if not (0 <= fan_id < self.fan_count):
            print(f"错误: 风扇编号 {fan_id} 超出范围")
            return 0

        if self.fg_pins_list[fan_id] is None:
            print(f"错误: 风扇 {fan_id+1} FG引脚未初始化")
            return 0

        return self._measure_frequency(fan_id)

    def read_fan_rpm(self, fan_id, pulses_per_revolution=2):
        """
        读取风扇实际转速 (RPM)
        fan_id: 风扇编号 (0-7)
        pulses_per_revolution: 每转脉冲数 (通常为2)
        返回: 风扇转速 (RPM)
        """
        frequency = self.read_fan_fg_frequency(fan_id)
        if frequency > 0:
            # RPM = 频率(Hz) * 60(秒/分钟) / 每转脉冲数
            rpm = (frequency * 60) / pulses_per_revolution
            return round(rpm, 1)
        else:
            return 0

    def read_all_fans_rpm(self, pulses_per_revolution=2):
        """
        读取所有风扇转速
        pulses_per_revolution: 每转脉冲数
        返回: 字典 {风扇编号: RPM}
        """
        rpm_data = {}
        for i in range(self.fan_count):
            rpm = self.read_fan_rpm(i, pulses_per_revolution)
            rpm_data[i] = rpm
        return rpm_data

    def read_fan_feedback(self, fan_id, threshold_rpm=500):
        """
        读取风扇反馈状态 (基于转速)
        fan_id: 风扇编号 (0-7)
        threshold_rpm: 判断风扇正常运行的最低转速阈值
        返回: True表示风扇正常，False表示异常或未连接
        """
        rpm = self.read_fan_rpm(fan_id)
        return rpm > threshold_rpm

    def read_all_fans_feedback(self, threshold_rpm=500):
        """
        读取所有风扇反馈状态
        threshold_rpm: 判断风扇正常运行的最低转速阈值
        返回: 字典 {风扇编号: 状态}
        """
        feedback_status = {}
        rpm_data = self.read_all_fans_rpm()
        for fan_id, rpm in rpm_data.items():
            feedback_status[fan_id] = rpm > threshold_rpm
        return feedback_status

    def stop_fan(self, fan_id):
        """
        停止指定风扇
        """
        return self.set_fan_speed(fan_id, 0)

    def stop_all_fans(self):
        """
        停止所有风扇
        """
        return self.set_all_fans_speed(0)

    def emergency_stop(self):
        """
        紧急停止所有风扇
        """
        print("紧急停止所有风扇!")
        for i in range(self.fan_count):
            if self.fan_pwms[i] is not None:
                self.fan_pwms[i].duty(0)
        return True

    def get_status_report(self, detailed=False):
        """
        获取系统状态报告
        detailed: 是否显示详细信息
        """
        print("\n=== 风扇控制系统状态报告 ===")

        # 读取所有风扇转速
        rpm_data = self.read_all_fans_rpm()
        # 读取所有风扇状态
        feedback_status = self.read_all_fans_feedback()

        for i in range(self.fan_count):
            if self.fan_pwms[i] is not None:
                current_duty = self.fan_pwms[i].duty()
                current_speed = int(current_duty * 100 / 1023)
                rpm = rpm_data[i]
                fg_freq = self.read_fan_fg_frequency(i)
                feedback_status_text = "正常" if feedback_status[i] else "异常"

                if detailed:
                    print(f"风扇 {i+1}: PWM {current_speed}% | RPM {rpm} | FG {fg_freq:.1f}Hz | {feedback_status_text}")
                else:
                    print(f"风扇 {i+1}: {current_speed}% | {rpm}RPM | {feedback_status_text}")
            else:
                print(f"风扇 {i+1}: 未初始化")

        print("=" * 50)
        return rpm_data

    def wait_for_rpm_stabilization(self, fan_id, target_rpm, timeout=10, tolerance=50):
        """
        等待风扇转速稳定到目标值
        fan_id: 风扇编号
        target_rpm: 目标转速
        timeout: 超时时间(秒)
        tolerance: 容差范围(RPM)
        返回: 是否成功稳定
        """
        start_time = time.ticks_ms()
        stable_count = 0
        required_stable_count = 3  # 连续3次测量在范围内才认为稳定

        while time.ticks_diff(time.ticks_ms(), start_time) < timeout * 1000:
            current_rpm = self.read_fan_rpm(fan_id)
            rpm_diff = abs(current_rpm - target_rpm)

            if rpm_diff <= tolerance:
                stable_count += 1
                if stable_count >= required_stable_count:
                    print(f"风扇 {fan_id+1} 转速稳定: {current_rpm}RPM")
                    return True
            else:
                stable_count = 0

            time.sleep(0.5)

        final_rpm = self.read_fan_rpm(fan_id)
        print(f"风扇 {fan_id+1} 稳定超时: {final_rpm}RPM (目标: {target_rpm}RPM)")
        return False