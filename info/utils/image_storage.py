from qiniu import Auth, put_data
# base64
access_key = 'bmnzYkDvbK4BFlQMdzL77cEMkBrqMbdsuPa5bykl'
secret_key = 'OUzMi0s1YTR0NjEq6nBCTwvNz3pV9AkMP5qjMnTQ'
# 七牛云创建的存储空间名称
bucket_name = 'newsli'


def storage(data):
    try:
        q = Auth(access_key, secret_key)
        token = q.upload_token(bucket_name)
        ret, info = put_data(token, None, data)
        print(ret, info)
    except Exception as e:
        raise e
    if info.status_code != 200:
        raise Exception('上传图片失败')
    return ret['key']


if __name__ == '__main__':
    file = input('请输入路径')
    with open(file, 'rb') as f:
        storage(f.read())


