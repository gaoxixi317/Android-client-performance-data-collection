import os,time,csv,re,threading,subprocess
from win32process import CREATE_NO_WINDOW

class AppClientPerformance:
    def __init__(self):
        self.cold_start_time_list = ["cold_start_time"]
        self.hot_start_time_list = ["hot_start_time"]
        self.cpu_usage_list=["cpu_usage"]
        self.memory_usage_list=["memory_usage"]
        self.battery_list=["battery"]
        self.send_bytes_list=["send_bytes"]
        self.receive_bytes_list=["receive_bytes"]


    def get_start_time(self,package_name,activity_name):
        #冷启动时间
        try:
            os.popen(f"adb shell am force-stop {package_name}")
        except:
            pass
        resp=os.popen(f"adb shell am  start -W -n {package_name}/{activity_name}")
        output=resp.read().strip()
        # print(output)
        cold_start_time=re.findall("TotalTime: (.*)",output)[0]
        self.cold_start_time_list.append(cold_start_time)
        # print(self.cold_start_time)
        time.sleep(3)
        #热启动时间
        os.popen(f"adb shell input keyevent 3")
        time.sleep(2)
        resp=os.popen(f"adb shell am  start -W -n {package_name}/{activity_name}")
        output = resp.read().strip()
        # print(output)
        hot_start_time = re.findall("TotalTime: (.*)", output)[0]
        self.hot_start_time_list.append(hot_start_time)
        # print(self.hot_start_time)


    def monitor_cpu(self,package_name):
        cmd=f"adb shell dumpsys cpuinfo | findstr {package_name}"
        resp=os.popen(cmd).read()
        cpu_usage=resp.strip().split("%")[0]
        # print(cpu_usage)
        self.cpu_usage_list.append(cpu_usage)
        # print(self.cpu_usage)

    def monitor_memory(self,package_name):
        output=os.popen(f"adb shell dumpsys meminfo | findstr {package_name}").read()
        # print(output)
        memory_usage=output.strip().split("kB:")[0]
        self.memory_usage_list.append(memory_usage)
        # print(self.memory_usage_list)

    def monitor_battery(self):
        output=os.popen(f"adb shell dumpsys battery").read()
        # print(output)
        battery=re.findall("level: (.*)",output)[0]
        self.battery_list.append(battery)
        # print(self.battery_list)

    def monitor_flow_bytes(self,package_name,inter_face="wlan0"):
        #查看进程，获取pid
        output=os.popen(f"adb shell ps |findstr {package_name}").read()
        # print(output)
        pid=output.strip().split()[1]
        #查看pid对应的流量
        output=os.popen(f"adb shell cat /proc/{pid}/net/dev").read()
        print(output)
        output = "#".join(output.split())
        # print(output)
        receive_bytes=re.findall(rf"#{inter_face}:#(\d*)#\d*#0#0#0#0#0#0#(\d*)",output)[0][0]
        send_bytes = re.findall(rf"#{inter_face}:#(\d*)#\d*#0#0#0#0#0#0#(\d*)", output)[0][1]
        self.receive_bytes_list.append(receive_bytes)
        self.send_bytes_list.append(send_bytes)
        # print(self.receive_bytes_list)
        # print(self.send_bytes_list)

    def get_performance(self,package_name,activity_name,inter_face="wlan0"):
        self.get_start_time(package_name,activity_name)
        print(f"正在收集性能信息。。。")
        while True:
            self.monitor_cpu(package_name)
            self.monitor_battery()
            self.monitor_memory(package_name)
            self.monitor_flow_bytes(package_name,inter_face)
            time.sleep(3)

    def app_operation(self,package_name):
        '''
        这里用monkey测试代替app的使用操作（也可根据需要自己写操作脚本）
        :param package_name:
        :return:
        '''
        cmd = f"adb shell monkey -p {package_name} -s 111 --monitor-native-crashes --pct-touch 50 --pct-motion 50 --pct-syskeys 0 --throttle 300 -v -v -v 1000"
        # os.system(cmd)#注：这里不能使用os.popen(),因为os.popen()是在后台执行的，而system是在前台执行的,这里需要前台执行的同时，利用多线程收集性能数据。
        subprocess.call(cmd, creationflags=CREATE_NO_WINDOW)

    def save_data(self):
        filename=time.strftime("%Y%m%d_%H%M%M.csv")
        try:
            os.mkdir(f"./performance_info")
        except:
            pass
        with open(f"./performance_info/performance_info{filename}","w",encoding='utf-8')as file:
            csv_writer=csv.writer(file)
            csv_writer.writerow(self.cold_start_time_list)
            csv_writer.writerow(self.hot_start_time_list)
            csv_writer.writerow(self.cpu_usage_list)
            csv_writer.writerow(self.battery_list)
            csv_writer.writerow(self.memory_usage_list)
            csv_writer.writerow(self.receive_bytes_list)
            csv_writer.writerow(self.send_bytes_list)

    def start_test(self, package_name, activity_name, inter_face="wlan0"):
        t = threading.Thread(target=self.get_performance, args=(package_name, activity_name, inter_face))
        t.setDaemon(True)
        t.start()
        self.app_operation(package_name)
        self.save_data()


if __name__ == '__main__':
    acp=AppClientPerformance()
    # acp.start_test("com.android.browser",".BrowserActivity",inter_face="eth1")
    # acp.start_test("com.android.packageinstaller", ".permission.ui.GrantPermissionsActivity")
    # acp.start_test("com.android.launcher3", "com.android.searchlauncher.SearchLauncher")
    acp.monitor_flow_bytes('com.android.launcher3')