"""
风扇系统简单测试程序
用于快速验证硬件连接和基本功能
支持FG信号转速测量
"""

from fan_controller import FanController
import time

def simple_test():
    """简单测试程序"""
    print("=== 风扇系统简单测试 (支持FG信号) ===")

    # 初始化控制器
    controller = FanController()

    print("\n1. 测试所有风扇50%转速...")
    controller.set_all_fans_speed(50)
    time.sleep(5)

    print("\n2. 检查风扇转速和FG信号...")
    print("等待转速稳定...")
    time.sleep(3)

    # 显示详细状态
    controller.get_status_report(detailed=True)

    print("\n3. 读取各风扇FG频率和转速...")
    for i in range(controller.fan_count):
        fg_freq = controller.read_fan_fg_frequency(i)
        rpm = controller.read_fan_rpm(i)
        print(f"风扇 {i + 1}: FG {fg_freq:.1f}Hz, RPM {rpm}")

    print("\n4. 测试单个风扇控制...")
    for i in range(controller.fan_count):
        print(f"\n测试风扇 {i + 1}:")

        print(f"  设置25%转速...")
        controller.set_fan_speed(i, 25)
        time.sleep(3)
        rpm = controller.read_fan_rpm(i)
        print(f"  实际转速: {rpm}RPM")

        print(f"  设置75%转速...")
        controller.set_fan_speed(i, 75)
        time.sleep(3)
        rpm = controller.read_fan_rpm(i)
        print(f"  实际转速: {rpm}RPM")

        print(f"  停止风扇...")
        controller.stop_fan(i)
        time.sleep(1)
        rpm = controller.read_fan_rpm(i)
        print(f"  停止后转速: {rpm}RPM")

    print("\n5. 紧急停止测试...")
    print("  启动所有风扇100%...")
    controller.set_all_fans_speed(100)
    time.sleep(3)

    print("  紧急停止!")
    controller.emergency_stop()

    print("\n6. 最终状态检查...")
    time.sleep(2)
    controller.get_status_report(detailed=True)

    print("\n测试完成!")
    return controller

def fg_signal_test():
    """FG信号专项测试"""
    print("=== FG信号专项测试 ===")

    controller = FanController()

    # 选择一个风扇进行详细测试
    test_fan = 0
    print(f"选择风扇 {test_fan + 1} 进行FG信号测试")

    speeds = [25, 50, 75, 100]

    for speed in speeds:
        print(f"\n设置转速 {speed}%...")
        controller.set_fan_speed(test_fan, speed)

        # 等待转速稳定
        time.sleep(4)

        # 多次读取FG频率和转速
        print("连续读取FG信号:")
        for j in range(5):
            fg_freq = controller.read_fan_fg_frequency(test_fan)
            rpm = controller.read_fan_rpm(test_fan)
            print(f"  测量 {j+1}: FG {fg_freq:.1f}Hz, RPM {rpm}")
            time.sleep(1)

    # 停止测试风扇
    controller.stop_fan(test_fan)
    print("\nFG信号测试完成")

if __name__ == "__main__":
    # 运行简单测试
    simple_test()

    # 可选：运行FG信号专项测试
    print("\n" + "="*50)
    fg_signal_test()