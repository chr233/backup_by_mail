#!/usr/bin/python3
import sys
import core
import traceback
from core import size2str, date2str, time2str, now


host_name = core.get_host_name()


def mail_log():
    '''发送系统报告邮件'''
    message, has_warn = core.gen_sys_info()
    if has_warn:
        subject = f'{date2str(now())}【{host_name}】系统报告【警告】'
    else:
        subject = f'{date2str(now())}【{host_name}】系统报告'
    core.send_email(subject, message)
    print(f'[{time2str(now())}]发送系统报告')


def mail_backup(path: str):
    file_list = core.sort_file_list(path)

    file_info, group_list = core.group_file_by_size(
        file_list, 50331648, 1048576
    )
    j = len(group_list)

    # 发送附件清单
    message = core.gen_file_info(file_info)
    subject = f'{date2str(now())}【{host_name}】附件清单【共{j}包】'
    core.send_email(subject, message)
    print(f'[{time2str(now())}]发送附件清单')

    # 发送每个附件包
    for i, group in enumerate(group_list, 1):
        subject = f'{date2str(now())}【{host_name}】附件包【第{i}/{j}包】'
        message = core.gen_pack_info(group)
        file_pack = core.pack_file(file_info, group)
        core.send_email(subject, message, file_pack)
        print(f'[{time2str(now())}]发送附件包【{i}/{j}】')


if __name__ == '__main__':
    try:
        print(f'[{date2str(now())}]开始运行,按Ctrl+C终止')
        path = sys.argv[1:2]
        if path:
            mail_backup(path[0])
        else:
            mail_log()
    except KeyboardInterrupt:
        print(f'[{time2str(now())}]终止执行')
    except Exception as e:
        print(f'[{time2str(now())}]程序出错{e}')
        traceback.print_exc()
    finally:
        print(f'[{date2str(now())}]运行结束')
