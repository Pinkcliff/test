#!/usr/bin/env python3
"""
系统集成测试和性能测试文件
测试整个风扇系统的集成功能、性能指标和稳定性
"""

import time
import statistics
import json
from datetime import datetime
from fan_controller import FanController
from config import PINS, PWM_FREQ, PWM_RESOLUTION


class SystemIntegrationTest:
    """系统集成测试类"""

    def __init__(self):
        self.controller = None
        self.test_results = []
        self.start_time = None

    def setup(self):
        """测试环境初始化"""
        print("初始化系统...")
        try:
            self.controller = FanController()
            self.start_time = time.time()
            print("✅ 系统初始化成功")
            return True
        except Exception as e:
            print(f"❌ 系统初始化失败: {e}")
            return False

    def cleanup(self):
        """测试清理"""
        if self.controller:
            self.controller.emergency_stop()
            print("🛑 系统已停止")

    def record_test_result(self, test_name, success, details=None, duration=None):
        """记录测试结果"""
        result = {
            'test_name': test_name,
            'success': success,
            'timestamp': datetime.now().isoformat(),
            'details': details,
            'duration': duration
        }
        self.test_results.append(result)

        # 输出结果
        status = "✅" if success else "❌"
        print(f"{status} {test_name}")
        if details:
            print(f"   详情: {details}")
        if duration:
            print(f"   耗时: {duration:.2f}秒")

    def test_basic_functionality(self):
        """测试基本功能"""
        print("\n=== 基本功能测试 ===")

        # 测试单风扇控制
        start_time = time.time()
        try:
            # 启动风扇0
            success = self.controller.set_fan_speed(0, 50)
            if not success:
                raise Exception("设置风扇速度失败")

            time.sleep(1)

            # 检查速度设置
            if self.controller.fan_speeds[0] != 50:
                raise Exception(f"速度设置错误: 期望50, 实际{self.controller.fan_speeds[0]}")

            # 停止风扇
            success = self.controller.set_fan_speed(0, 0)
            if not success:
                raise Exception("停止风扇失败")

            duration = time.time() - start_time
            self.record_test_result("单风扇控制测试", True, "成功启动和停止风扇", duration)

        except Exception as e:
            duration = time.time() - start_time
            self.record_test_result("单风扇控制测试", False, str(e), duration)

        # 测试多风扇控制
        start_time = time.time()
        try:
            speeds = [25, 50, 75, 100, 33, 66, 88, 11]
            success = self.controller.set_all_fans_speed(speeds)
            if not success:
                raise Exception("设置所有风扇速度失败")

            time.sleep(2)

            # 验证速度设置
            for i, expected_speed in enumerate(speeds):
                if self.controller.fan_speeds[i] != expected_speed:
                    raise Exception(f"风扇{i}速度设置错误: 期望{expected_speed}, 实际{self.controller.fan_speeds[i]}")

            # 停止所有风扇
            self.controller.set_all_fans_speed([0] * 8)

            duration = time.time() - start_time
            self.record_test_result("多风扇控制测试", True, "成功控制8个风扇", duration)

        except Exception as e:
            duration = time.time() - start_time
            self.record_test_result("多风扇控制测试", False, str(e), duration)

    def test_fg_signal_functionality(self):
        """测试FG信号功能"""
        print("\n=== FG信号功能测试 ===")

        start_time = time.time()
        try:
            # 启动一个风扇用于测试
            self.controller.set_fan_speed(0, 75)
            self.controller.stopped = False

            # 等待几秒让风扇稳定
            time.sleep(3)

            # 读取频率
            frequency = self.controller.read_fan_fg_frequency(0)
            rpm = self.controller.read_fan_rpm(0)

            if frequency <= 0:
                raise Exception(f"FG频率读取失败: {frequency}Hz")

            if rpm <= 0:
                raise Exception(f"RPM计算失败: {rpm}")

            # 验证RPM计算合理性
            expected_rpm = (frequency / 2) * 60  # 假设每转2个脉冲
            rpm_error = abs(rpm - expected_rpm) / expected_rpm

            if rpm_error > 0.1:  # 允许10%误差
                raise Exception(f"RPM计算误差过大: {rpm_error:.2%}")

            duration = time.time() - start_time
            details = f"频率: {frequency:.1f}Hz, RPM: {rpm:.0f}, 误差: {rpm_error:.2%}"
            self.record_test_result("FG信号读取测试", True, details, duration)

            # 停止风扇
            self.controller.set_fan_speed(0, 0)

        except Exception as e:
            duration = time.time() - start_time
            self.record_test_result("FG信号读取测试", False, str(e), duration)

    def test_speed_stability(self):
        """测试转速稳定性"""
        print("\n=== 转速稳定性测试 ===")

        start_time = time.time()
        try:
            # 设置风扇速度
            target_speed = 60
            self.controller.set_fan_speed(0, target_speed)
            self.controller.stopped = False

            # 等待速度稳定
            stable = self.controller.wait_for_speed_stability(0, 3000)  # 目标3000 RPM

            if not stable:
                raise Exception("转速未能在预期时间内稳定")

            # 连续读取RPM值，检查稳定性
            rpm_readings = []
            for _ in range(10):
                rpm = self.controller.read_fan_rpm(0)
                rpm_readings.append(rpm)
                time.sleep(0.5)

            # 计算统计信息
            avg_rpm = statistics.mean(rpm_readings)
            rpm_std = statistics.stdev(rpm_readings)
            cv = rpm_std / avg_rpm  # 变异系数

            if cv > 0.05:  # 变异系数超过5%认为不稳定
                raise Exception(f"转速不稳定，变异系数: {cv:.2%}")

            duration = time.time() - start_time
            details = f"平均RPM: {avg_rpm:.0f}, 标准差: {rpm_std:.1f}, 变异系数: {cv:.2%}"
            self.record_test_result("转速稳定性测试", True, details, duration)

            # 停止风扇
            self.controller.set_fan_speed(0, 0)

        except Exception as e:
            duration = time.time() - start_time
            self.record_test_result("转速稳定性测试", False, str(e), duration)

    def test_emergency_stop(self):
        """测试紧急停止功能"""
        print("\n=== 紧急停止测试 ===")

        start_time = time.time()
        try:
            # 启动多个风扇
            speeds = [50, 75, 100, 60, 80, 40, 90, 70]
            self.controller.set_all_fans_speed(speeds)

            time.sleep(1)

            # 执行紧急停止
            self.controller.emergency_stop()

            # 验证所有风扇已停止
            for i, speed in enumerate(self.controller.fan_speeds):
                if speed != 0:
                    raise Exception(f"风扇{i}未正确停止，速度: {speed}")

            if not self.controller.stopped:
                raise Exception("系统停止标志未正确设置")

            duration = time.time() - start_time
            self.record_test_result("紧急停止测试", True, "所有风扇成功停止", duration)

        except Exception as e:
            duration = time.time() - start_time
            self.record_test_result("紧急停止测试", False, str(e), duration)

    def test_performance_metrics(self):
        """测试性能指标"""
        print("\n=== 性能指标测试 ===")

        # 测试PWM响应时间
        start_time = time.time()
        try:
            # 测试PWM设置响应时间
            response_times = []
            for speed in [25, 50, 75, 100]:
                t1 = time.time()
                self.controller.set_fan_speed(0, speed)
                t2 = time.time()
                response_times.append((t2 - t1) * 1000)  # 转换为毫秒

            avg_response_time = statistics.mean(response_times)
            max_response_time = max(response_times)

            if avg_response_time > 10:  # 平均响应时间超过10ms认为过慢
                raise Exception(f"PWM响应时间过慢: {avg_response_time:.2f}ms")

            duration = time.time() - start_time
            details = f"平均响应: {avg_response_time:.2f}ms, 最大响应: {max_response_time:.2f}ms"
            self.record_test_result("PWM响应性能测试", True, details, duration)

        except Exception as e:
            duration = time.time() - start_time
            self.record_test_result("PWM响应性能测试", False, str(e), duration)

        # 测试FG读取频率
        start_time = time.time()
        try:
            self.controller.set_fan_speed(0, 80)
            self.controller.stopped = False

            time.sleep(2)  # 等待风扇稳定

            # 测试连续读取速度
            read_times = []
            for _ in range(100):
                t1 = time.time()
                self.controller.read_fan_rpm(0)
                t2 = time.time()
                read_times.append((t2 - t1) * 1000)  # 转换为毫秒

            avg_read_time = statistics.mean(read_times)
            max_read_time = max(read_times)
            read_frequency = 1000 / avg_read_time  # Hz

            if read_frequency < 100:  # 读取频率低于100Hz认为过慢
                raise Exception(f"FG读取频率过低: {read_frequency:.1f}Hz")

            duration = time.time() - start_time
            details = f"读取频率: {read_frequency:.1f}Hz, 平均耗时: {avg_read_time:.2f}ms"
            self.record_test_result("FG读取性能测试", True, details, duration)

            self.controller.set_fan_speed(0, 0)

        except Exception as e:
            duration = time.time() - start_time
            self.record_test_result("FG读取性能测试", False, str(e), duration)

    def test_system_stability(self):
        """测试系统稳定性"""
        print("\n=== 系统稳定性测试 ===")

        start_time = time.time()
        try:
            # 长时间运行测试
            test_duration = 60  # 60秒测试
            self.controller.stopped = False

            # 启动所有风扇
            speeds = [30, 45, 60, 75, 40, 55, 70, 85]
            self.controller.set_all_fans_speed(speeds)

            error_count = 0
            total_readings = 0

            end_time = time.time() + test_duration
            while time.time() < end_time:
                try:
                    # 随机读取不同风扇的RPM
                    for fan_id in range(8):
                        rpm = self.controller.read_fan_rpm(fan_id)
                        total_readings += 1

                        # 检查RPM值是否合理
                        if rpm < 0 or rpm > 30000:  # 假设最大转速30000
                            error_count += 1

                    time.sleep(0.1)

                except Exception:
                    error_count += 1

            # 计算错误率
            error_rate = error_count / total_readings if total_readings > 0 else 1

            if error_rate > 0.01:  # 错误率超过1%认为不稳定
                raise Exception(f"系统不稳定，错误率: {error_rate:.2%}")

            duration = time.time() - start_time
            details = f"测试时长: {test_duration}秒, 错误率: {error_rate:.2%}, 总读取: {total_readings}"
            self.record_test_result("系统稳定性测试", True, details, duration)

            # 停止所有风扇
            self.controller.set_all_fans_speed([0] * 8)

        except Exception as e:
            duration = time.time() - start_time
            self.record_test_result("系统稳定性测试", False, str(e), duration)

    def test_memory_usage(self):
        """测试内存使用情况"""
        print("\n=== 内存使用测试 ===")

        start_time = time.time()
        try:
            # 在MicroPython中，我们可以通过创建对象来模拟内存压力
            import gc

            # 记录初始内存状态
            gc.collect()
            initial_free = gc.mem_free()

            # 执行一系列操作
            for _ in range(1000):
                self.controller.read_all_fans_rpm()
                self.controller.get_status_report()

            # 强制垃圾回收
            gc.collect()
            final_free = gc.mem_free()

            memory_used = initial_free - final_free
            if memory_used < 0:
                memory_used = 0

            # 检查内存泄漏
            if memory_used > 10240:  # 超过10KB认为可能有内存泄漏
                raise Exception(f"可能存在内存泄漏，使用内存: {memory_used} bytes")

            duration = time.time() - start_time
            details = f"内存使用: {memory_used} bytes, 可用内存: {final_free} bytes"
            self.record_test_result("内存使用测试", True, details, duration)

        except Exception as e:
            duration = time.time() - start_time
            self.record_test_result("内存使用测试", False, str(e), duration)

    def run_all_tests(self):
        """运行所有集成测试"""
        print("🚀 开始系统集成测试")
        print("=" * 50)

        if not self.setup():
            return False

        try:
            # 运行各项测试
            self.test_basic_functionality()
            self.test_fg_signal_functionality()
            self.test_speed_stability()
            self.test_emergency_stop()
            self.test_performance_metrics()
            self.test_system_stability()
            self.test_memory_usage()

            # 生成测试报告
            self.generate_test_report()

            # 计算成功率
            total_tests = len(self.test_results)
            passed_tests = sum(1 for r in self.test_results if r['success'])
            success_rate = passed_tests / total_tests if total_tests > 0 else 0

            print("\n" + "=" * 50)
            print(f"测试完成: {passed_tests}/{total_tests} 通过 ({success_rate:.1%})")

            return success_rate >= 0.8  # 80%以上通过率认为成功

        finally:
            self.cleanup()

    def generate_test_report(self):
        """生成测试报告"""
        report = {
            'test_session': {
                'start_time': self.start_time,
                'end_time': time.time(),
                'total_duration': time.time() - self.start_time,
                'total_tests': len(self.test_results),
                'passed_tests': sum(1 for r in self.test_results if r['success']),
                'failed_tests': sum(1 for r in self.test_results if not r['success'])
            },
            'test_results': self.test_results,
            'system_info': {
                'pwm_frequency': PWM_FREQ,
                'pwm_resolution': PWM_RESOLUTION,
                'total_fans': 8
            }
        }

        # 保存到文件
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"test_report_{timestamp}.json"

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            print(f"\n📄 测试报告已保存: {filename}")
        except Exception as e:
            print(f"\n❌ 保存测试报告失败: {e}")


def run_integration_tests():
    """运行集成测试的主函数"""
    tester = SystemIntegrationTest()
    return tester.run_all_tests()


def main():
    """主函数"""
    print("ESP32 8通道风扇控制系统 - 集成测试")
    print("=" * 50)

    success = run_integration_tests()

    if success:
        print("\n🎉 集成测试通过！系统运行正常。")
        return 0
    else:
        print("\n⚠️ 集成测试未完全通过，请检查系统状态。")
        return 1


if __name__ == "__main__":
    exit(main())