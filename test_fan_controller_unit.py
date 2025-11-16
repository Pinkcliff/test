#!/usr/bin/env python3
"""
FanController单元测试文件
测试风扇控制器的核心功能，包括PWM控制、FG信号读取、RPM计算等
"""

import time
import unittest
from unittest.mock import Mock, patch, MagicMock
from fan_controller import FanController
from config import PINS, PWM_FREQ, PWM_RESOLUTION


class TestFanControllerUnit(unittest.TestCase):
    """FanController类的单元测试"""

    def setUp(self):
        """测试前的设置"""
        # 模拟硬件环境
        self.mock_machine = Mock()
        self.mock_pin = Mock()
        self.mock_pwm = Mock()
        self.mock_extint = Mock()

        # 模拟引脚配置
        with patch('machine.Pin', self.mock_pin), \
             patch('machine.PWM', self.mock_pwm), \
             patch('machine.ExtInt', self.mock_extint):

            self.fan_controller = FanController()

    def test_initialization(self):
        """测试控制器初始化"""
        # 验证PWM初始化次数
        self.assertEqual(self.mock_pwm.call_count, 8)

        # 验证外部中断初始化次数
        self.assertEqual(self.mock_extint.call_count, 8)

        # 验证所有风扇初始速度为0
        for speed in self.fan_controller.fan_speeds:
            self.assertEqual(speed, 0)

        # 验证所有风扇初始脉冲计数为0
        for count in self.fan_controller.pulse_counts:
            self.assertEqual(count, 0)

        # 验证初始停止状态
        self.assertTrue(self.fan_controller.stopped)

    def test_set_fan_speed(self):
        """测试单个风扇速度设置"""
        # 设置风扇0速度为50%
        result = self.fan_controller.set_fan_speed(0, 50)
        self.assertTrue(result)
        self.assertEqual(self.fan_controller.fan_speeds[0], 50)

        # 测试无效风扇编号
        result = self.fan_controller.set_fan_speed(8, 50)
        self.assertFalse(result)

        # 测试负速度
        result = self.fan_controller.set_fan_speed(0, -10)
        self.assertFalse(result)

        # 测试超过100的速度
        result = self.fan_controller.set_fan_speed(0, 110)
        self.assertFalse(result)

        # 测试0速度（停止）
        result = self.fan_controller.set_fan_speed(0, 0)
        self.assertTrue(result)
        self.assertEqual(self.fan_controller.fan_speeds[0], 0)

    def test_set_all_fans_speed(self):
        """测试所有风扇速度设置"""
        speeds = [25, 50, 75, 100, 0, 33, 66, 88]
        result = self.fan_controller.set_all_fans_speed(speeds)
        self.assertTrue(result)

        # 验证所有速度设置正确
        for i, speed in enumerate(speeds):
            self.assertEqual(self.fan_controller.fan_speeds[i], speed)

        # 测试无效长度的速度数组
        result = self.fan_controller.set_all_fans_speed([50, 75])
        self.assertFalse(result)

        # 测试包含无效值
        result = self.fan_controller.set_all_fans_speed([25, 50, 150, 75, 33, 66, 88, 99])
        self.assertFalse(result)

    def test_speed_to_duty_cycle_conversion(self):
        """测试速度到占空比的转换"""
        # 测试边界值
        self.assertEqual(self.fan_controller._speed_to_duty_cycle(0), 0)
        self.assertEqual(self.fan_controller._speed_to_duty_cycle(100), 1023)

        # 测试中间值
        self.assertEqual(self.fan_controller._speed_to_duty_cycle(50), 512)
        self.assertEqual(self.fan_controller._speed_to_duty_cycle(25), 256)
        self.assertEqual(self.fan_controller._speed_to_duty_cycle(75), 767)

    def test_fg_interrupt_handler(self):
        """测试FG中断处理函数"""
        # 模拟中断触发
        self.fan_controller.stopped = False

        # 测试通道0的中断处理
        self.fan_controller._fg_interrupt_handler(0)
        self.assertEqual(self.fan_controller.pulse_counts[0], 1)
        self.assertGreater(self.fan_controller.pulse_times[0], 0)

        # 测试多个脉冲
        for i in range(10):
            self.fan_controller._fg_interrupt_handler(0)

        self.assertEqual(self.fan_controller.pulse_counts[0], 11)

    def test_read_fan_fg_frequency(self):
        """测试风扇FG频率读取"""
        # 模拟脉冲数据
        self.fan_controller.pulse_counts[0] = 100
        self.fan_controller.pulse_times[0] = time.time() - 1.0  # 1秒前
        self.fan_controller.pulse_start_times[0] = time.time() - 1.0

        frequency = self.fan_controller.read_fan_fg_frequency(0)
        self.assertEqual(frequency, 100.0)  # 100脉冲/秒

        # 测试无脉冲情况
        self.fan_controller.pulse_counts[0] = 0
        frequency = self.fan_controller.read_fan_fg_frequency(0)
        self.assertEqual(frequency, 0.0)

        # 测试无效通道
        frequency = self.fan_controller.read_fan_fg_frequency(8)
        self.assertEqual(frequency, 0.0)

    def test_read_fan_rpm(self):
        """测试风扇RPM读取"""
        # 模拟频率数据（假设每转2个脉冲）
        self.fan_controller.pulse_counts[0] = 200  # 200脉冲/秒
        self.fan_controller.pulse_times[0] = time.time() - 1.0
        self.fan_controller.pulse_start_times[0] = time.time() - 1.0

        rpm = self.fan_controller.read_fan_rpm(0)
        self.assertEqual(rpm, 6000.0)  # 200脉冲/秒 / 2脉冲/转 * 60秒/分钟

        # 测试0频率
        self.fan_controller.pulse_counts[0] = 0
        rpm = self.fan_controller.read_fan_rpm(0)
        self.assertEqual(rpm, 0.0)

    def test_read_all_fans_rpm(self):
        """测试读取所有风扇RPM"""
        # 设置不同的脉冲计数
        for i in range(8):
            self.fan_controller.pulse_counts[i] = (i + 1) * 50
            self.fan_controller.pulse_times[i] = time.time() - 1.0
            self.fan_controller.pulse_start_times[i] = time.time() - 1.0

        rpms = self.fan_controller.read_all_fans_rpm()
        expected = [1500, 3000, 4500, 6000, 7500, 9000, 10500, 12000]
        self.assertEqual(rpms, expected)

    def test_emergency_stop(self):
        """测试紧急停止功能"""
        # 设置一些风扇速度
        self.fan_controller.set_fan_speed(0, 75)
        self.fan_controller.set_fan_speed(1, 50)

        # 执行紧急停止
        self.fan_controller.emergency_stop()

        # 验证所有速度设置为0
        for speed in self.fan_controller.fan_speeds:
            self.assertEqual(speed, 0)

        # 验证停止标志
        self.assertTrue(self.fan_controller.stopped)

    def test_wait_for_speed_stability(self):
        """测试转速稳定等待功能"""
        # 模拟稳定的转速数据
        target_rpm = 3000.0

        # 第一次读取，不稳定
        with patch.object(self.fan_controller, 'read_fan_rpm') as mock_rpm:
            mock_rpm.return_value = 2000.0
            result = self.fan_controller.wait_for_speed_stability(0, target_rpm)
            self.assertFalse(result)

        # 模拟稳定转速
        with patch.object(self.fan_controller, 'read_fan_rpm') as mock_rpm:
            mock_rpm.return_value = 3050.0  # 在容差范围内
            result = self.fan_controller.wait_for_speed_stability(0, target_rpm)
            self.assertTrue(result)

    def test_read_fan_feedback(self):
        """测试风扇反馈读取"""
        # 模拟RPM数据
        test_rpm = 2500.0

        with patch.object(self.fan_controller, 'read_fan_rpm') as mock_rpm:
            mock_rpm.return_value = test_rpm

            feedback = self.fan_controller.read_fan_feedback(0)
            self.assertEqual(feedback['fan_id'], 0)
            self.assertEqual(feedback['speed_percent'], self.fan_controller.fan_speeds[0])
            self.assertEqual(feedback['rpm'], test_rpm)
            self.assertIn('timestamp', feedback)

        # 测试无效通道
        feedback = self.fan_controller.read_fan_feedback(8)
        self.assertIsNone(feedback)

    def test_get_status_report(self):
        """测试状态报告生成"""
        # 设置一些测试数据
        self.fan_controller.set_fan_speed(0, 50)

        with patch.object(self.fan_controller, 'read_all_fans_rpm') as mock_rpms:
            mock_rpms.return_value = [1500, 0, 0, 0, 0, 0, 0, 0]

            report = self.fan_controller.get_status_report()

            # 验证报告结构
            self.assertIn('timestamp', report)
            self.assertIn('system_stopped', report)
            self.assertIn('fans', report)
            self.assertIn('total_active_fans', report)

            # 验证风扇数据
            fan_data = report['fans'][0]
            self.assertEqual(fan_data['fan_id'], 0)
            self.assertEqual(fan_data['speed_percent'], 50)
            self.assertEqual(fan_data['rpm'], 1500)
            self.assertTrue(fan_data['active'])


class TestFanControllerEdgeCases(unittest.TestCase):
    """测试边缘情况和异常处理"""

    def setUp(self):
        """测试前的设置"""
        with patch('machine.Pin'), \
             patch('machine.PWM'), \
             patch('machine.ExtInt'):
            self.fan_controller = FanController()

    def test_negative_pulses_handling(self):
        """测试负脉冲计数的处理"""
        # 故意设置负数
        self.fan_controller.pulse_counts[0] = -10

        frequency = self.fan_controller.read_fan_fg_frequency(0)
        self.assertEqual(frequency, 0.0)  # 应该返回0而不是负数

    def test_extreme_values(self):
        """测试极值处理"""
        # 测试极高频率
        self.fan_controller.pulse_counts[0] = 1000000  # 1MHz
        self.fan_controller.pulse_times[0] = time.time() - 0.001  # 1ms

        frequency = self.fan_controller.read_fan_fg_frequency(0)
        self.assertGreater(frequency, 0)

        # 测试极大RPM
        rpm = self.fan_controller.read_fan_rpm(0)
        self.assertGreater(rpm, 0)

    def test_concurrent_interrupts(self):
        """测试并发中断处理"""
        self.fan_controller.stopped = False

        # 模拟快速连续中断
        for _ in range(1000):
            self.fan_controller._fg_interrupt_handler(0)

        self.assertEqual(self.fan_controller.pulse_counts[0], 1000)


def run_unit_tests():
    """运行所有单元测试"""
    print("开始运行FanController单元测试...")

    # 创建测试套件
    test_suite = unittest.TestSuite()

    # 添加测试用例
    test_suite.addTest(unittest.makeSuite(TestFanControllerUnit))
    test_suite.addTest(unittest.makeSuite(TestFanControllerEdgeCases))

    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)

    # 输出结果
    if result.wasSuccessful():
        print("\n✅ 所有单元测试通过！")
        return True
    else:
        print(f"\n❌ 测试失败: {len(result.failures)} 个失败, {len(result.errors)} 个错误")
        return False


if __name__ == "__main__":
    run_unit_tests()