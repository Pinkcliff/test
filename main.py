"""
ESP32 风扇控制系统主程序
运行在ESP32上，提供完整的8通道风扇控制功能
"""

from fan_controller import FanController
import time
import machine

class FanSystemManager:
    def __init__(self):
        print("启动风扇控制系统...")
        self.controller = FanController()
        self.running = True

        # 内置LED用于状态指示
        try:
            self.led = machine.Pin(2, machine.Pin.OUT)
            self.led.off()
        except:
            self.led = None
            print("警告: 无法初始化状态LED")

    def status_blink(self, count=1):
        """LED状态指示"""
        if self.led:
            for _ in range(count):
                self.led.on()
                time.sleep(0.1)
                self.led.off()
                time.sleep(0.1)

    def test_all_fans(self):
        """测试所有风扇功能"""
        print("\n=== 开始风扇功能测试 (支持FG信号) ===")

        # 测试每个风扇单独控制
        for fan_id in range(self.controller.fan_count):
            print(f"\n测试风扇 {fan_id + 1}")

            # 读取初始状态
            initial_rpm = self.controller.read_fan_rpm(fan_id)
            initial_fg = self.controller.read_fan_fg_frequency(fan_id)
            print(f"初始状态: FG {initial_fg:.1f}Hz, RPM {initial_rpm}")

            # 设置中等转速
            print("设置50%转速...")
            self.controller.set_fan_speed(fan_id, 50)
            time.sleep(4)  # 等待转速稳定

            # 读取运行状态
            running_rpm = self.controller.read_fan_rpm(fan_id)
            running_fg = self.controller.read_fan_fg_frequency(fan_id)
            print(f"运行状态: FG {running_fg:.1f}Hz, RPM {running_rpm}")

            # 测试不同转速
            for speed in [25, 75]:
                print(f"设置{speed}%转速...")
                self.controller.set_fan_speed(fan_id, speed)
                time.sleep(3)

                test_rpm = self.controller.read_fan_rpm(fan_id)
                test_fg = self.controller.read_fan_fg_frequency(fan_id)
                print(f"测试结果: FG {test_fg:.1f}Hz, RPM {test_rpm}")

            # 停止风扇
            print("停止风扇...")
            self.controller.stop_fan(fan_id)
            time.sleep(2)

            stop_rpm = self.controller.read_fan_rpm(fan_id)
            stop_fg = self.controller.read_fan_fg_frequency(fan_id)
            print(f"停止后: FG {stop_fg:.1f}Hz, RPM {stop_rpm}")

            self.status_blink(1)

        print("\n=== 风扇测试完成 ===")

    def demo_speed_control(self):
        """演示风扇速度控制"""
        print("\n=== 风扇速度控制演示 (FG信号监测) ===")

        # 渐进式调速演示
        speeds = [25, 50, 75, 100, 75, 50, 25, 0]

        for speed in speeds:
            print(f"\n设置所有风扇转速为: {speed}%")
            self.controller.set_all_fans_speed(speed)

            # 等待转速稳定
            if speed > 0:
                print("等待转速稳定...")
                time.sleep(4)

            # 显示详细状态
            print("当前风扇状态:")
            self.controller.get_status_report(detailed=True)

            # 显示平均转速
            rpm_data = self.controller.read_all_fans_rpm()
            active_rpm = [rpm for rpm in rpm_data.values() if rpm > 0]
            if active_rpm:
                avg_rpm = sum(active_rpm) / len(active_rpm)
                print(f"平均转速: {avg_rpm:.1f}RPM")

            self.status_blink(2)
            time.sleep(2)

        print("\n速度控制演示完成")

    def monitor_mode(self, duration=60):
        """监控模式，持续监控风扇状态"""
        print(f"\n=== 进入监控模式 ({duration}秒) - FG信号实时监测 ===")

        start_time = time.ticks_ms()

        while time.ticks_diff(time.ticks_ms(), start_time) < duration * 1000:
            elapsed_seconds = time.ticks_diff(time.ticks_ms(), start_time) // 1000
            print(f"\n时间: {elapsed_seconds}秒")

            # 显示基本状态
            self.controller.get_status_report()

            # 显示FG信号详细信息
            print("FG信号详情:")
            for i in range(self.controller.fan_count):
                fg_freq = self.controller.read_fan_fg_frequency(i)
                rpm = self.controller.read_fan_rpm(i)
                status = "运行" if rpm > 500 else "停止"
                print(f"  风扇{i+1}: {fg_freq:.1f}Hz | {rpm}RPM | {status}")

            # LED闪烁表示监控中
            self.status_blink(1)

            time.sleep(5)  # 每5秒检查一次

        print(f"\n监控模式结束，共监控 {duration} 秒")

    def emergency_stop_demo(self):
        """紧急停止演示"""
        print("\n=== 紧急停止演示 ===")

        # 启动所有风扇
        print("启动所有风扇...")
        self.controller.set_all_fans_speed(80)
        time.sleep(3)

        # 紧急停止
        print("执行紧急停止!")
        self.controller.emergency_stop()

        self.status_blink(5)  # 快速闪烁表示紧急停止
        print("紧急停止完成")

    def run_interactive_demo(self):
        """交互式演示"""
        print("\n=== 交互式演示模式 (支持FG信号) ===")
        print("使用终端控制风扇:")
        print("  fan <编号> <转速>  - 控制单个风扇")
        print("  all <转速>        - 控制所有风扇")
        print("  stop              - 停止所有风扇")
        print("  status            - 查看基本状态")
        print("  detail            - 查看详细状态")
        print("  rpm <编号>        - 查看指定风扇转速")
        print("  fg <编号>         - 查看指定风扇FG频率")
        print("  allrpm            - 查看所有风扇转速")
        print("  test              - 运行测试")
        print("  quit              - 退出")

        while self.running:
            try:
                command = input("\n请输入命令: ").strip().lower()

                if command == "quit":
                    self.running = False
                    break
                elif command == "stop":
                    self.controller.stop_all_fans()
                    print("所有风扇已停止")
                elif command == "status":
                    self.controller.get_status_report()
                elif command == "detail":
                    self.controller.get_status_report(detailed=True)
                elif command == "allrpm":
                    rpm_data = self.controller.read_all_fans_rpm()
                    print("所有风扇转速:")
                    for fan_id, rpm in rpm_data.items():
                        print(f"  风扇{fan_id+1}: {rpm}RPM")
                elif command.startswith("rpm "):
                    parts = command.split()
                    if len(parts) == 2:
                        fan_id = int(parts[1]) - 1
                        rpm = self.controller.read_fan_rpm(fan_id)
                        fg_freq = self.controller.read_fan_fg_frequency(fan_id)
                        print(f"风扇{fan_id+1}: {rpm}RPM, FG频率: {fg_freq:.1f}Hz")
                    else:
                        print("格式: rpm <编号>")
                elif command.startswith("fg "):
                    parts = command.split()
                    if len(parts) == 2:
                        fan_id = int(parts[1]) - 1
                        fg_freq = self.controller.read_fan_fg_frequency(fan_id)
                        print(f"风扇{fan_id+1} FG频率: {fg_freq:.1f}Hz")
                    else:
                        print("格式: fg <编号>")
                elif command == "test":
                    self.test_all_fans()
                elif command.startswith("fan "):
                    parts = command.split()
                    if len(parts) == 3:
                        fan_id = int(parts[1]) - 1
                        speed = int(parts[2])
                        self.controller.set_fan_speed(fan_id, speed)
                        print(f"风扇{fan_id+1}设置为{speed}%转速")
                        time.sleep(2)  # 等待转速变化
                        rpm = self.controller.read_fan_rpm(fan_id)
                        print(f"实际转速: {rpm}RPM")
                    else:
                        print("格式: fan <编号> <转速>")
                elif command.startswith("all "):
                    parts = command.split()
                    if len(parts) == 2:
                        speed = int(parts[1])
                        self.controller.set_all_fans_speed(speed)
                        print(f"所有风扇设置为{speed}%转速")
                        time.sleep(3)  # 等待转速稳定
                        self.controller.get_status_report()
                    else:
                        print("格式: all <转速>")
                else:
                    print("未知命令，请重新输入")

            except KeyboardInterrupt:
                print("\n收到中断信号...")
                self.controller.emergency_stop()
                break
            except Exception as e:
                print(f"错误: {e}")

    def cleanup(self):
        """清理资源"""
        print("\n正在清理资源...")
        self.controller.emergency_stop()
        print("系统已安全关闭")

def main():
    """主函数"""
    try:
        # 创建系统管理器
        manager = FanSystemManager()

        print("\n风扇控制系统启动成功!")
        print("系统功能:")
        print("1. 支持8路风扇独立PWM控制")
        print("2. 支持风扇状态反馈监测")
        print("3. 提供紧急停止功能")
        print("4. 实时状态监控")

        # 运行完整的演示程序
        manager.status_blink(3)

        # 1. 基础功能测试
        manager.test_all_fans()
        time.sleep(2)

        # 2. 速度控制演示
        manager.demo_speed_control()
        time.sleep(2)

        # 3. 紧急停止演示
        manager.emergency_stop_demo()
        time.sleep(2)

        # 4. 监控模式演示
        manager.monitor_mode(30)

        # 5. 交互式演示
        manager.run_interactive_demo()

    except KeyboardInterrupt:
        print("\n程序被用户中断")
    except Exception as e:
        print(f"程序运行错误: {e}")
    finally:
        if 'manager' in locals():
            manager.cleanup()

if __name__ == "__main__":
    main()