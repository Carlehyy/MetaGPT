#!/usr/bin/env python3
import requests
import yaml
import json

def get_tenant_access_token(app_id, app_secret):
    """获取飞书tenant_access_token"""
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    headers = {"Content-Type": "application/json"}
    data = {"app_id": app_id, "app_secret": app_secret}

    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        result = response.json()

        if result.get("code") == 0:
            return result.get("tenant_access_token"), None
        else:
            return None, f"获取token失败: {result}"
    except Exception as e:
        return None, f"请求异常: {e}"

# 读取配置
with open('/opt/ai-team/config.yaml', 'r') as f:
    config = yaml.safe_load(f)

app_id = config['feishu']['app_id']
app_secret = config['feishu']['app_secret']

print(f"测试飞书API连接...")
print(f"AppID: {app_id[:10]}...")

token, error = get_tenant_access_token(app_id, app_secret)

if token:
    print("✅ 飞书API连接成功！")
    print(f"✅ Token获取成功: {token[:20]}...")

    # 测试获取应用信息
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get("https://open.feishu.cn/open-apis/application/v6/applications", headers=headers)
    if resp.status_code == 200:
        print("✅ 应用API调用成功")
    else:
        print(f"⚠️ 应用API调用返回: {resp.status_code}")
else:
    print(f"❌ 飞书API连接失败: {error}")
