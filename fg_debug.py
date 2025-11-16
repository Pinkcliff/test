"""
FG信号调试工具
用于调试和验证风扇FG信号
"""

from fan_controller import FanController
import time

def fg_signal_debug():
    """FG信号详细调试"""
    print("=== FG信号调试工具 ===")

    controller = FanController()

    # 选择要调试的风扇
    print("\n请选择要调试的风扇编号 (1-8):")
    try:
        fan_num = int(input("风扇编号: ")) - 1
        if not (0 <= fan_num < controller.fan_count):
            print("错误: 风扇编号超出范围")
            return
    except:
        print("输入错误，使用默认风扇1")
        fan_num = 0

    print(f"\n开始调试风扇 {fan_num + 1}")
    print("请确保风扇已正确连接")

    # 测试不同转速下的FG信号
    speeds = [0, 25, 50, 75, 100]

    for speed in speeds:
        print(f"\n{'='*40}")
        print(f"测试转速: {speed}%")
        print(f"{'='*40}")

        # 设置转速
        controller.set_fan_speed(fan_num, speed)

        if speed == 0:
            print("等待风扇停止...")
        else:
            print("等待转速稳定...")

        time.sleep(4)

        # 多次测量FG信号
        print("开始FG信号测量:")
        measurements = []

        for i in range(10):
            # 测量FG频率
            fg_freq = controller.read_fan_fg_frequency(fan_num)
            # 测量转速
            rpm = controller.read_fan_rpm(fan_num)

            measurements.append((fg_freq, rpm))
            print(f"  测量 {i+1:2d}: FG {fg_freq:6.1f}Hz | RPM {rpm:6.1f}")

            time.sleep(1)

        # 统计分析
        if speed > 0:
            valid_measurements = [m for m in measurements if m[0] > 0]
            if valid_measurements:
                avg_fg = sum(m[0] for m in valid_measurements) / len(valid_measurements)
                avg_rpm = sum(m[1] for m in valid_measurements) / len(valid_measurements)
                max_fg = max(m[0] for m in valid_measurements)
                min_fg = min(m[0] for m in valid_measurements)

                print(f"\n统计分析 (有效测量 {len(valid_measurements)}/10):")
                print(f"  平均FG频率: {avg_fg:.1f}Hz")
                print(f"  平均转速: {avg_rpm:.1f}RPM")
                print(f"  FG频率范围: {min_fg:.1f}Hz - {max_fg:.1f}Hz")
                print(f"  FG频率稳定性: {((1 - (max_fg - min_fg) / avg_fg) * 100):.1f}%")

                # 计算每转脉冲数
                if avg_fg > 0:
                    pulses_per_rev = (avg_fg * 60) / avg_rpm if avg_rpm > 0 else 0
                    print(f"  计算每转脉冲数: {pulses_per_rev:.2f}")
            else:
                print("  警告: 未检测到有效的FG信号!")
        else:
            # 检查停止时是否有误信号
            false_signals = [m for m in measurements if m[0] > 0]
            if false_signals:
                print(f"  警告: 风扇停止时检测到 {len(false_signals)} 个误信号")
            else:
                print("  正常: 风扇停止时无FG信号")

        # 等待下次测试
        print("\n按回车键继续下一个测试...")
        try:
            input()
        except KeyboardInterrupt:
            print("\n用户中断测试")
            break

    # 停止风扇
    controller.stop_fan(fan_num)
    print("\n调试完成，风扇已停止")

def continuous_monitor():
    """连续监控模式"""
    print("=== FG信号连续监控 ===")

    controller = FanController()

    print("\n设置所有风扇为50%转速...")
    controller.set_all_fans_speed(50)
    time.sleep(5)

    print("开始连续监控 (按Ctrl+C停止):")

    try:
        while True:
            print(f"\n时间: {time.ticks_ms() // 1000}秒")
            print("-" * 60)

            for i in range(controller.fan_count):
                fg_freq = controller.read_fan_fg_frequency(i)
                rpm = controller.read_fan_rpm(i)

                status = "正常" if rpm > 500 else "停止"
                signal_quality = "良好" if fg_freq > 0 else "无信号"

                print(f"风扇{i+1:2d}: FG {fg_freq:6.1f}Hz | RPM {rpm:6.1f} | {status} | {signal_quality}")

            time.sleep(2)

    except KeyboardInterrupt:
        print("\n监控停止")

    finally:
        controller.stop_all_fans()
        print("所有风扇已停止")

def pulse_analysis():
    """脉冲分析模式"""
    print("=== FG脉冲分析 ===")

    controller = FanController()

    # 测试单个风扇的脉冲计数
    test_fan = 0
    print(f"分析风扇 {test_fan + 1}")

    # 重置计数器
    controller.fg_counters[test_fan] = 0
    controller.fg_last_time[test_fan] = time.ticks_ms()

    print("设置风扇为75%转速...")
    controller.set_fan_speed(test_fan, 75)
    time.sleep(3)

    print("开始脉冲计数分析 (每秒显示一次):")
    print("时间(s) | 脉冲数 | 频率(Hz) | RPM")
    print("-" * 40)

    start_time = time.ticks_ms()
    last_count = 0

    try:
        for i in range(20):  # 运行20秒
            time.sleep(1)

            current_time = time.ticks_ms()
            elapsed = time.ticks_diff(current_time, start_time) / 1000

            # 获取当前计数
            current_count = controller.fg_counters[test_fan]

            # 计算这一秒的脉冲数
            pulses_this_second = current_count - last_count
            last_count = current_count

            # 计算频率和转速
            frequency = pulses_this_second  # Hz
            rpm = (frequency * 60) / 2  # 假设每转2个脉冲

            print(f"{elapsed:6.1f} | {pulses_this_second:6d} | {frequency:8.1f} | {rpm:6.1f}")

    except KeyboardInterrupt:
        print("\n分析中断")

    finally:
        controller.stop_fan(test_fan)
        print("分析完成")

if __name__ == "__main__":
    print("FG信号调试工具")
    print("1. FG信号详细调试")
    print("2. 连续监控模式")
    print("3. 脉冲分析模式")

    try:
        choice = input("请选择调试模式 (1-3): ").strip()

        if choice == "1":
            fg_signal_debug()
        elif choice == "2":
            continuous_monitor()
        elif choice == "3":
            pulse_analysis()
        else:
            print("无效选择")
    except KeyboardInterrupt:
        print("\n程序退出")
    except Exception as e:
        print(f"错误: {e}")