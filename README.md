# szu-schedule-ical
这是一个从深圳大学网上办事大厅（Ehall）提取课程表数据，生成iCal格式文件（.ics），
从而实现**全平台**原生日历显示课表的工具。

目前，该工具仅适用于本科生。

## 特点
- 在Windows、macOS、iOS、Android、Windows Phone等系统，以及各大邮箱服务，都有着强大的原生支持
- 免去第三方课表应用的流氓推广、无用社交功能，以及保持后台提醒推送时的耗电情况，实现功能的轻量化
- 得益于云同步的功能，只需一个设备导入课表，其他关联设备都可同步显示


## 如何运行此脚本
```
# 下载代码
git clone https://github.com/NagaruZ/szu-schedule-ical.git
cd szu-schedule-ical

# 创建虚拟环境
python -m venv venv
.\venv\Scripts\activate    # Windows
source ./venv/bin/activate # Linux

# 安装依赖
pip install -r requirements.txt

# 运行
python script.py     # Windows
python3 script.py    # Linux
```
然后根据提示，依次：
- 输入当前学期（```学年-学期号```的形式，如2019-2020学年的第二个学期，即为```2019-2020-2```）
- 输入学期第一周的周一日期
- 选择当前学期的课程时间安排
- 统一认证系统的用户名（学号）及密码
- 课前提醒时间

操作完成后，会在脚本目录下生成```schedule.ics```。
## iCal文件使用方法
请参阅[华南师范大学 iCal课表使用指引](https://i.scnu.edu.cn/ical/doc#%E5%AF%BC%E5%85%A5%E7%9A%84%E6%AD%A5%E9%AA%A4)。

开发者注：

由于不同平台对iCal格式标准中“事件提醒”的实现不一，课前提醒的功能可能会受到影响。
在QQ邮箱导入本工具生成的iCal文件，事件可正常显示，但提醒会丢失；
若此前生成iCal时设置了需要提醒，在Outlook.com导入时会提示失败。（下个版本会尝试解决此问题）

经过自己的测试，目前有一个无损导入事件提醒的做法：

对于Android平台，首先使用Exchange与某个邮箱服务相关联，
然后使用[iCal Import/Export CalDAV for Android](https://apkpure.com/ical-import-export-caldav/tk.drlue.icalimportexport)
导入iCal文件到相应的日历下，这样在可以保留通知的同时使用Exchange同步。

## 隐私声明
本工具需要您提供统一认证登录的用户名和密码。该登录凭据只会用于在网上办事大厅（Ehall）模拟登录以获取您的课程表信息。
本工具不会持久化存储您的登录凭据，也不会使用它访问、获取、存储、修改您的其他个人信息。

您若使用本工具，就代表着您已知悉上述声明。

## 致谢
感谢[CCZU-iCal](https://github.com/Hogan-TR/CCZU-iCal)提供思路，并从中参考了部分文字说明。
