"""
API 工具模块 - 用于调用DeepSeek API进行文本生成
"""
import os
import json
import time
import requests
from typing import Dict, Any, Optional


def get_api_key() -> str:
    """获取API密钥"""
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        raise ValueError("未设置DEEPSEEK_API_KEY环境变量")
    return api_key


def call_api(
    prompt: str,
    model: str = "deepseek-chat",
    temperature: float = 0.7,
    max_tokens: int = 4000,
    max_retries: int = 3,
    retry_delay: int = 5
) -> str:
    """
    调用DeepSeek API进行文本生成
    
    参数:
        prompt: 提示文本
        model: 使用的模型名称
        temperature: 温度参数，控制随机性
        max_tokens: 最大生成的token数量
        max_retries: 最大重试次数
        retry_delay: 重试间隔（秒）
        
    返回:
        生成的文本
    """
    api_key = get_api_key()
    url = "https://api.deepseek.com/v1/chat/completions"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    data = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": temperature,
        "max_tokens": max_tokens
    }
    
    for attempt in range(max_retries):
        try:
            response = requests.post(url, headers=headers, json=data, timeout=120)
            response.raise_for_status()  # 如果响应状态不是2xx，抛出HTTPError异常
            
            result = response.json()
            if "choices" in result and result["choices"]:
                return result["choices"][0]["message"]["content"]
            else:
                raise ValueError(f"API返回无效结果: {result}")
                
        except requests.exceptions.RequestException as e:
            print(f"API请求失败 (尝试 {attempt+1}/{max_retries}): {str(e)}")
            
            if attempt < max_retries - 1:
                print(f"等待 {retry_delay} 秒后重试...")
                time.sleep(retry_delay)
            else:
                raise RuntimeError(f"API请求失败，已达到最大重试次数: {str(e)}")
    
    raise RuntimeError("无法连接到API服务")


def mock_api_call(prompt: str) -> str:
    """
    模拟API调用，用于测试或离线开发
    仅返回简单的模拟数据
    """
    print("使用模拟API (仅用于测试)")
    
    # 根据提示中的关键词返回不同的模拟响应
    if "生成测试数据" in prompt:
        return json.dumps({
            "test_cases": [
                {
                    "id": "1",
                    "input": "3\n1 2 3",
                    "output": "6"
                },
                {
                    "id": "2",
                    "input": "5\n1 2 3 4 5",
                    "output": "15"
                }
            ]
        })
    else:
        return json.dumps({
            "title": "数组求和",
            "description": "给定一个整数数组，求所有元素的和。",
            "difficulty": 1,
            "time_limit": 1000,
            "memory_limit": 128,
            "input_format": "第一行一个整数n，表示数组长度。\n第二行n个整数，表示数组元素。",
            "output_format": "输出一个整数，表示数组所有元素的和。",
            "sample_input": "3\n1 2 3",
            "sample_output": "6"
        }) 