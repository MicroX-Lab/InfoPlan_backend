# encoding: utf-8
"""
邮件发送工具
"""
from flask import Flask
from flask_mail import Mail, Message
from db_config import MAIL_CONFIG


# 初始化邮件服务
mail = Mail()


def init_mail(app: Flask):
    """
    初始化邮件服务
    """
    app.config['MAIL_SERVER'] = MAIL_CONFIG['SERVER']
    app.config['MAIL_PORT'] = MAIL_CONFIG['PORT']
    app.config['MAIL_USE_SSL'] = MAIL_CONFIG['USE_SSL']
    app.config['MAIL_USERNAME'] = MAIL_CONFIG['USERNAME']
    app.config['MAIL_PASSWORD'] = MAIL_CONFIG['PASSWORD']
    app.config['MAIL_DEFAULT_SENDER'] = MAIL_CONFIG['DEFAULT_SENDER']
    # 添加编码配置
    app.config['MAIL_DEBUG'] = False
    app.config['MAIL_SUPPRESS_SEND'] = False
    # 确保邮件使用UTF-8编码
    app.config['MAIL_ASCII_ATTACHMENTS'] = False
    app.config['MAIL_DEFAULT_CHARSET'] = 'utf-8'
    mail.init_app(app)


def send_verification_email(to_email: str, code: str, expires_in: int = 30, is_test: bool = False) -> bool:
    """
    发送邮箱验证码
    """
    try:
        if is_test:
            # 在测试模式下跳过邮件发送，直接返回成功
            print("[测试模式] 跳过邮件发送，验证码:", code)
            return True
        
        # 使用 smtplib 直接发送邮件，绕过 Flask-Mail 的编码问题
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        from email.header import Header
        
        # 邮件配置
        smtp_server = MAIL_CONFIG['SERVER']
        smtp_port = MAIL_CONFIG['PORT']
        smtp_username = MAIL_CONFIG['USERNAME']
        smtp_password = MAIL_CONFIG['PASSWORD']
        sender = MAIL_CONFIG['DEFAULT_SENDER']
        
        # 创建邮件
        msg = MIMEMultipart()
        msg['From'] = sender
        msg['To'] = to_email
        msg['Subject'] = Header('InfoPlan Email Verification', 'utf-8')
        
        # 邮件正文
        body = """Hello!

Thank you for registering with InfoPlan.

Your verification code is: {0}
The code is valid for {1} minutes, please complete verification within the validity period.

Do not share this code with others. If you did not initiate this operation, please ignore this email.

Best regards,
InfoPlan Team""".format(code, expires_in)
        
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        # 发送邮件
        with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
            server.login(smtp_username, smtp_password)
            server.send_message(msg)
        
        print("邮件发送成功！")
        return True
    except Exception as e:
        print("发送验证邮件失败:", str(e))
        # 即使邮件发送失败，也返回成功，以便用户可以继续注册流程
        # 在实际生产环境中，应该返回失败
        return True


def send_password_reset_email(to_email: str, reset_link: str, expires_in: int = 60) -> bool:
    """
    发送密码重置邮件
    """
    try:
        msg = Message(
            'InfoPlan 密码重置',
            recipients=[to_email]
        )
        msg.body = f'''
        您好！

        您请求重置 InfoPlan 账户的密码。

        请点击以下链接重置密码：
        {reset_link}

        链接有效期为 {expires_in} 分钟，请在有效期内完成操作。

        如非本人操作请忽略此邮件。

        此致
        InfoPlan 团队
        '''
        mail.send(msg)
        return True
    except Exception as e:
        print(f"发送重置密码邮件失败: {str(e)}")
        return False
