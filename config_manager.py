#!/usr/bin/env python3
"""
配置管理工具
提供系统配置的查看、修改和保存功能
"""

import json
import copy
from datetime import datetime
from config import *


class ConfigManager:
    """配置管理器"""

    def __init__(self):
        self.config = {
            'pins': PINS,
            'pwm': {
                'frequency': PWM_FREQ,
                'resolution': PWM_RESOLUTION
            },
            'system': {
                'timeout': SYSTEM_TIMEOUT,
                'stability_threshold': STABILITY_THRESHOLD,
                'stability_wait_time': STABILITY_WAIT_TIME
            },
            'fans': {
                'pulses_per_revolution': PULSES_PER_REVOLUTION,
                'min_rpm': MIN_RPM,
                'max_rpm': MAX_RPM
            },
            'error_handling': ERROR_HANDLING
        }
        self.original_config = copy.deepcopy(self.config)

    def show_config(self):
        """显示当前配置"""
        print("\n⚙️  系统配置")
        print("=" * 50)

        # 引脚配置
        print("\n📌 引脚配置:")
        print(f"  控制引脚: {self.config['pins']['control']}")
        print(f"  FG引脚: {self.config['pins']['fg']}")

        # PWM配置
        print("\n📊 PWM配置:")
        print(f"  频率: {self.config['pwm']['frequency']} Hz")
        print(f"  分辨率: {self.config['pwm']['resolution']} 位")

        # 系统配置
        print("\n🖥️  系统配置:")
        print(f"  超时时间: {self.config['system']['timeout']} 秒")
        print(f"  稳定性阈值: {self.config['system']['stability_threshold']} %")
        print(f"  稳定等待时间: {self.config['system']['stability_wait_time']} 秒")

        # 风扇配置
        print("\n🌀 风扇配置:")
        print(f"  每转脉冲数: {self.config['fans']['pulses_per_revolution']}")
        print(f"  最小RPM: {self.config['fans']['min_rpm']}")
        print(f"  最大RPM: {self.config['fans']['max_rpm']}")

        # 错误处理配置
        print("\n⚠️  错误处理:")
        for key, value in self.config['error_handling'].items():
            print(f"  {key}: {value}")

    def edit_config(self):
        """编辑配置"""
        print("\n✏️  配置编辑")
        print("-" * 30)

        while True:
            print("\n选择要编辑的配置项:")
            print("1. PWM频率")
            print("2. 系统超时时间")
            print("3. 稳定性阈值")
            print("4. 每转脉冲数")
            print("5. 完成编辑")

            choice = input("\n请选择 (1-5): ").strip()

            if choice == '1':
                try:
                    freq = int(input(f"PWM频率 (当前: {self.config['pwm']['frequency']} Hz): "))
                    if 1000 <= freq <= 50000:
                        self.config['pwm']['frequency'] = freq
                        print(f"✅ PWM频率已更新为 {freq} Hz")
                    else:
                        print("❌ 频率范围应在 1000-50000 Hz")
                except ValueError:
                    print("❌ 输入格式错误")

            elif choice == '2':
                try:
                    timeout = float(input(f"系统超时时间 (当前: {self.config['system']['timeout']} 秒): "))
                    if 1 <= timeout <= 300:
                        self.config['system']['timeout'] = timeout
                        print(f"✅ 超时时间已更新为 {timeout} 秒")
                    else:
                        print("❌ 超时时间应在 1-300 秒")
                except ValueError:
                    print("❌ 输入格式错误")

            elif choice == '3':
                try:
                    threshold = float(input(f"稳定性阈值 (当前: {self.config['system']['stability_threshold']} %): "))
                    if 1 <= threshold <= 50:
                        self.config['system']['stability_threshold'] = threshold
                        print(f"✅ 稳定性阈值已更新为 {threshold} %")
                    else:
                        print("❌ 阈值应在 1-50 %")
                except ValueError:
                    print("❌ 输入格式错误")

            elif choice == '4':
                try:
                    pulses = int(input(f"每转脉冲数 (当前: {self.config['fans']['pulses_per_revolution']}): "))
                    if 1 <= pulses <= 10:
                        self.config['fans']['pulses_per_revolution'] = pulses
                        print(f"✅ 每转脉冲数已更新为 {pulses}")
                    else:
                        print("❌ 脉冲数应在 1-10")
                except ValueError:
                    print("❌ 输入格式错误")

            elif choice == '5':
                break

            else:
                print("❌ 无效选择")

    def reset_config(self):
        """重置配置为默认值"""
        print("\n🔄 重置配置")
        confirm = input("确认重置所有配置为默认值? (y/N): ").strip().lower()

        if confirm == 'y':
            self.config = copy.deepcopy(self.original_config)
            print("✅ 配置已重置为默认值")
        else:
            print("❌ 操作已取消")

    def save_config(self, filename=None):
        """保存配置到文件"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"config_{timestamp}.json"

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)

            print(f"✅ 配置已保存到: {filename}")
            return True
        except Exception as e:
            print(f"❌ 保存配置失败: {e}")
            return False

    def load_config(self, filename):
        """从文件加载配置"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                loaded_config = json.load(f)

            # 验证配置结构
            required_keys = ['pins', 'pwm', 'system', 'fans', 'error_handling']
            if all(key in loaded_config for key in required_keys):
                self.config = loaded_config
                print(f"✅ 配置已从 {filename} 加载")
                return True
            else:
                print("❌ 配置文件格式错误")
                return False

        except FileNotFoundError:
            print(f"❌ 文件不存在: {filename}")
            return False
        except json.JSONDecodeError:
            print(f"❌ JSON格式错误: {filename}")
            return False
        except Exception as e:
            print(f"❌ 加载配置失败: {e}")
            return False

    def validate_config(self):
        """验证配置的有效性"""
        print("\n🔍 配置验证")
        errors = []

        # 验证PWM配置
        pwm_freq = self.config['pwm']['frequency']
        if not (1000 <= pwm_freq <= 50000):
            errors.append(f"PWM频率超出范围: {pwm_freq}")

        # 验证系统配置
        timeout = self.config['system']['timeout']
        if not (1 <= timeout <= 300):
            errors.append(f"系统超时时间超出范围: {timeout}")

        threshold = self.config['system']['stability_threshold']
        if not (1 <= threshold <= 50):
            errors.append(f"稳定性阈值超出范围: {threshold}")

        # 验证风扇配置
        pulses = self.config['fans']['pulses_per_revolution']
        if not (1 <= pulses <= 10):
            errors.append(f"每转脉冲数超出范围: {pulses}")

        min_rpm = self.config['fans']['min_rpm']
        max_rpm = self.config['fans']['max_rpm']
        if min_rpm >= max_rpm:
            errors.append("最小RPM应小于最大RPM")

        # 验证引脚配置
        control_pins = self.config['pins']['control']
        fg_pins = self.config['pins']['fg']
        if len(control_pins) != 8 or len(fg_pins) != 8:
            errors.append("引脚配置数量错误")

        # 验证引脚冲突
        all_pins = control_pins + fg_pins
        if len(all_pins) != len(set(all_pins)):
            errors.append("存在引脚冲突")

        if errors:
            print("❌ 发现配置错误:")
            for error in errors:
                print(f"  • {error}")
            return False
        else:
            print("✅ 配置验证通过")
            return True

    def export_config_code(self):
        """导出配置为Python代码"""
        print("\n📄 导出配置代码")

        config_code = f'''# 自动生成的配置文件
# 生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

# 引脚配置
PINS = {{
    'control': {self.config['pins']['control']},
    'fg': {self.config['pins']['fg']}
}}

# PWM配置
PWM_FREQ = {self.config['pwm']['frequency']}
PWM_RESOLUTION = {self.config['pwm']['resolution']}

# 系统配置
SYSTEM_TIMEOUT = {self.config['system']['timeout']}
STABILITY_THRESHOLD = {self.config['system']['stability_threshold']}
STABILITY_WAIT_TIME = {self.config['system']['stability_wait_time']}

# 风扇配置
PULSES_PER_REVOLUTION = {self.config['fans']['pulses_per_revolution']}
MIN_RPM = {self.config['fans']['min_rpm']}
MAX_RPM = {self.config['fans']['max_rpm']}

# 错误处理配置
ERROR_HANDLING = {self.config['error_handling']}
'''

        filename = f"generated_config_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(config_code)
            print(f"✅ 配置代码已导出到: {filename}")
            return True
        except Exception as e:
            print(f"❌ 导出失败: {e}")
            return False


def main():
    """主函数"""
    print("🛠️  配置管理工具")
    print("=" * 40)

    manager = ConfigManager()

    while True:
        print("\n📋 主菜单:")
        print("1. 查看当前配置")
        print("2. 编辑配置")
        print("3. 验证配置")
        print("4. 保存配置")
        print("5. 加载配置")
        print("6. 重置配置")
        print("7. 导出配置代码")
        print("8. 退出")

        choice = input("\n请选择 (1-8): ").strip()

        if choice == '1':
            manager.show_config()

        elif choice == '2':
            manager.edit_config()

        elif choice == '3':
            manager.validate_config()

        elif choice == '4':
            filename = input("保存文件名 (回车自动生成): ").strip()
            if not filename:
                filename = None
            manager.save_config(filename)

        elif choice == '5':
            filename = input("配置文件路径: ").strip()
            if filename:
                manager.load_config(filename)

        elif choice == '6':
            manager.reset_config()

        elif choice == '7':
            manager.export_config_code()

        elif choice == '8':
            print("👋 退出程序")
            break

        else:
            print("❌ 无效选择")

    return 0


if __name__ == "__main__":
    exit(main())