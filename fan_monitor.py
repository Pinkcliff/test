#!/usr/bin/env python3
"""
风扇系统监控工具
提供实时监控、数据记录和可视化功能
"""

import time
import json
import csv
from datetime import datetime
from fan_controller import FanController


class FanMonitor:
    """风扇监控类"""

    def __init__(self):
        self.controller = None
        self.monitoring = False
        self.data_log = []
        self.log_file = None

    def start(self):
        """启动监控系统"""
        try:
            self.controller = FanController()
            print("✅ 风扇监控系统已启动")
            return True
        except Exception as e:
            print(f"❌ 启动失败: {e}")
            return False

    def stop(self):
        """停止监控系统"""
        if self.controller:
            self.controller.emergency_stop()
        if self.log_file:
            self.log_file.close()
        print("🛑 监控系统已停止")

    def set_fan_speeds(self, speeds):
        """设置风扇速度"""
        if isinstance(speeds, list):
            return self.controller.set_all_fans_speed(speeds)
        else:
            # 单个速度，应用到所有风扇
            all_speeds = [speeds] * 8
            return self.controller.set_all_fans_speed(all_speeds)

    def get_current_status(self):
        """获取当前状态"""
        if not self.controller:
            return None

        rpms = self.controller.read_all_fans_rpm()
        status = {
            'timestamp': datetime.now().isoformat(),
            'fan_speeds': self.controller.fan_speeds.copy(),
            'fan_rpms': rpms,
            'active_fans': sum(1 for rpm in rpms if rpm > 0),
            'system_stopped': self.controller.stopped
        }
        return status

    def print_status(self, status):
        """打印状态信息"""
        print(f"\n📊 系统状态 - {status['timestamp'][:19]}")
        print("-" * 60)
        print(f"风扇 | 速度(%) | RPM     | 状态")
        print("-" * 60)

        for i in range(8):
            speed = status['fan_speeds'][i]
            rpm = status['fan_rpms'][i]
            status_icon = "🟢" if rpm > 0 else "🔴"
            print(f"  {i:2d} |   {speed:3d}   | {rpm:6.0f} | {status_icon}")

        print("-" * 60)
        print(f"活动风扇: {status['active_fans']}/8")
        print(f"系统状态: {'运行中' if not status['system_stopped'] else '已停止'}")

    def start_logging(self, filename=None):
        """开始数据记录"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"fan_log_{timestamp}.csv"

        try:
            self.log_file = open(filename, 'w', newline='')
            writer = csv.writer(self.log_file)

            # 写入CSV头部
            headers = ['timestamp'] + \
                     [f'fan_{i}_speed' for i in range(8)] + \
                     [f'fan_{i}_rpm' for i in range(8)] + \
                     ['active_fans', 'system_stopped']
            writer.writerow(headers)

            print(f"📝 开始记录数据到: {filename}")
            return True
        except Exception as e:
            print(f"❌ 无法创建日志文件: {e}")
            return False

    def log_data(self, status):
        """记录数据"""
        if not self.log_file:
            return

        try:
            writer = csv.writer(self.log_file)
            row = [
                status['timestamp'],
                *status['fan_speeds'],
                *status['fan_rpms'],
                status['active_fans'],
                int(status['system_stopped'])
            ]
            writer.writerow(row)
            self.log_file.flush()  # 确保数据写入
        except Exception as e:
            print(f"❌ 写入日志失败: {e}")

    def monitor_realtime(self, interval=1.0, duration=60):
        """实时监控"""
        print(f"🔍 开始实时监控，间隔: {interval}秒，时长: {duration}秒")
        self.monitoring = True

        start_time = time.time()
        last_log_time = start_time

        while self.monitoring and (time.time() - start_time) < duration:
            try:
                status = self.get_current_status()
                if status:
                    # 清屏并显示状态
                    print("\033[2J\033[H")  # ANSI清屏
                    self.print_status(status)

                    # 记录数据
                    if time.time() - last_log_time >= 5:  # 每5秒记录一次
                        self.log_data(status)
                        self.data_log.append(status)
                        last_log_time = time.time()

                    # 显示剩余时间
                    remaining = duration - (time.time() - start_time)
                    print(f"\n⏱️  剩余时间: {remaining:.0f}秒")

                time.sleep(interval)

            except KeyboardInterrupt:
                print("\n⚠️ 用户中断监控")
                break
            except Exception as e:
                print(f"❌ 监控错误: {e}")

        self.monitoring = False
        print("\n✅ 监控完成")

    def analyze_data(self):
        """分析记录的数据"""
        if not self.data_log:
            print("❌ 没有数据可分析")
            return

        print("\n📈 数据分析报告")
        print("=" * 50)

        # 基本统计
        total_records = len(self.data_log)
        print(f"记录总数: {total_records}")

        # 分析每个风扇
        for fan_id in range(8):
            fan_rpms = [record['fan_rpms'][fan_id] for record in self.data_log]
            active_rpms = [rpm for rpm in fan_rpms if rpm > 0]

            if active_rpms:
                avg_rpm = sum(active_rpms) / len(active_rpms)
                min_rpm = min(active_rpms)
                max_rpm = max(active_rpms)
                uptime = len(active_rpms) / total_records * 100

                print(f"\n风扇 {fan_id}:")
                print(f"  平均RPM: {avg_rpm:.0f}")
                print(f"  最小RPM: {min_rpm:.0f}")
                print(f"  最大RPM: {max_rpm:.0f}")
                print(f"  运行时间: {uptime:.1f}%")
            else:
                print(f"\n风扇 {fan_id}: 未运行")

        # 系统整体状态
        total_active = sum(record['active_fans'] for record in self.data_log)
        avg_active = total_active / total_records
        print(f"\n系统平均活动风扇数: {avg_active:.1f}")

    def save_analysis(self, filename=None):
        """保存分析结果"""
        if not self.data_log:
            return False

        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"fan_analysis_{timestamp}.json"

        analysis = {
            'metadata': {
                'total_records': len(self.data_log),
                'time_range': {
                    'start': self.data_log[0]['timestamp'],
                    'end': self.data_log[-1]['timestamp']
                }
            },
            'fan_statistics': {},
            'raw_data': self.data_log
        }

        # 计算每个风扇的统计信息
        for fan_id in range(8):
            rpms = [record['fan_rpms'][fan_id] for record in self.data_log]
            active_rpms = [rpm for rpm in rpms if rpm > 0]

            if active_rpms:
                analysis['fan_statistics'][f'fan_{fan_id}'] = {
                    'average_rpm': sum(active_rpms) / len(active_rpms),
                    'min_rpm': min(active_rpms),
                    'max_rpm': max(active_rpms),
                    'uptime_percentage': len(active_rpms) / len(self.data_log) * 100
                }

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(analysis, f, indent=2, ensure_ascii=False)
            print(f"📊 分析结果已保存: {filename}")
            return True
        except Exception as e:
            print(f"❌ 保存分析失败: {e}")
            return False


def main():
    """主函数"""
    print("🌡️  风扇系统监控工具")
    print("=" * 40)

    monitor = FanMonitor()

    if not monitor.start():
        return 1

    try:
        # 用户交互菜单
        while True:
            print("\n📋 选择操作:")
            print("1. 设置风扇速度")
            print("2. 查看当前状态")
            print("3. 开始实时监控")
            print("4. 分析历史数据")
            print("5. 退出")

            choice = input("\n请选择 (1-5): ").strip()

            if choice == '1':
                try:
                    print("\n输入风扇速度设置:")
                    print("a. 统一设置所有风扇")
                    print("b. 分别设置每个风扇")

                    sub_choice = input("选择 (a/b): ").strip().lower()

                    if sub_choice == 'a':
                        speed = int(input("设置速度 (0-100): "))
                        if 0 <= speed <= 100:
                            monitor.set_fan_speeds(speed)
                            print(f"✅ 所有风扇设置为 {speed}%")
                        else:
                            print("❌ 速度范围错误")
                    elif sub_choice == 'b':
                        speeds = []
                        for i in range(8):
                            speed = int(input(f"风扇 {i} 速度 (0-100): "))
                            speeds.append(speed)
                        monitor.set_fan_speeds(speeds)
                        print("✅ 风扇速度设置完成")
                    else:
                        print("❌ 无效选择")

                except ValueError:
                    print("❌ 输入格式错误")

            elif choice == '2':
                status = monitor.get_current_status()
                if status:
                    monitor.print_status(status)

            elif choice == '3':
                try:
                    interval = float(input("监控间隔 (秒, 默认1.0): ") or "1.0")
                    duration = float(input("监控时长 (秒, 默认60): ") or "60")

                    # 开始数据记录
                    monitor.start_logging()

                    # 开始监控
                    monitor.monitor_realtime(interval, duration)

                    # 分析数据
                    monitor.analyze_data()
                    monitor.save_analysis()

                except ValueError:
                    print("❌ 输入格式错误")

            elif choice == '4':
                monitor.analyze_data()

            elif choice == '5':
                print("👋 退出程序")
                break

            else:
                print("❌ 无效选择")

    except KeyboardInterrupt:
        print("\n⚠️ 用户中断")
    finally:
        monitor.stop()

    return 0


if __name__ == "__main__":
    exit(main())