import pexpect

def run_command(command):
    """
    执行命令并捕获输出（适用于 Python 或其他交互式命令）
    
    Args:
        command (str): 要执行的命令（如 "python3 -c 'print(\"Hello\")'"）
    
    Returns:
        tuple: (output: str, child: pexpect.spawn)  # 输出字符串和子进程对象
    """
    child = pexpect.spawn('/bin/bash', ['-c', command], encoding='utf-8')
    child.logfile = open('/tmp/pexpect.log', 'w')  # 用于调试
    
    try:
        # 捕获所有输出，直到进程结束
        child.expect(pexpect.EOF, timeout=90)
        output = child.before  # 获取全部输出
    except pexpect.exceptions.TIMEOUT:
        print(f"Timeout: {command} did not finish in time.")
        output = child.before  # 超时前已输出的内容
    finally:
        child.logfile.close()
    
    return output, child  # 返回输出字符串和子进程对象（可选）

command = 'cd /home/adminpc/DucoCobotAPI/DucoCobotAPI_py && python SiasunRobot.py'
output, child = run_command(command)
print("Python 输出:", output)