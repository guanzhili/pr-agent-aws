from flask import Flask, request
import subprocess
import shlex

app = Flask(__name__)

# 定义触发关键词
REVIEW_TRIGGER = '/aws_review'

@app.route('/github-webhook', methods=['POST'])
def github_webhook():
    data = request.json
    print(f"Received webhook data: {data}")
    
    action = data.get('action')
    print(f"Triggering Python task with action: {action}")
    
    # 检查是否是评论事件
    if action == 'created':
        comment = data['comment']['body']
        
        # 检查comment中是否包含 REVIEW_TRIGGER（用于提取后面的内容）
        if REVIEW_TRIGGER in comment:
            pr_url = data['issue']['pull_request']['html_url']
            # 去掉 REVIEW_TRIGGER 部分，获取剩余的评论内容
            comment_content = comment.replace(REVIEW_TRIGGER, '').strip()
            
            # 调用 Python 任务，传递 PR URL 和评论内容
            trigger_python_task(pr_url, comment_content)
    
    return '', 200


@app.route('/gitlab-webhook', methods=['POST'])
def gitlab_webhook():
    data = request.json
    print(f"Received webhook data: {data}")
    
    # 检查是否为评论事件
    if 'object_attributes' in data and data['object_attributes']['noteable_type'] == 'MergeRequest':
        comment = data['object_attributes']['note']
        
        print(f"full comment is: {comment}")

        # 检查评论中是否包含 REVIEW_TRIGGER
        if REVIEW_TRIGGER in comment:
            print(f"full comment contains: {REVIEW_TRIGGER}")
            pr_url = data['merge_request']['url']
            
            # 去掉 REVIEW_TRIGGER 部分，获取剩余的评论内容
            comment_content = comment.replace(REVIEW_TRIGGER, '').strip()
            
            # 调用 Python 任务，传递 PR URL 和评论内容
            trigger_python_task(pr_url, comment_content)
    
    return '', 200

import subprocess

def trigger_python_task(pr_url, comment):
    # 执行命令并捕获输出
    print(f"Debug message: pr_url is {pr_url}")
    print(f"Debug message: comment is {comment}")
    comment = comment.replace('"', '').replace("'", '')
    cmd = ['python3', '-m', 'pr_agent.cli', '--pr_url', pr_url] + shlex.split(comment)
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    # 打印命令的标准输出
    print("Standard Output:")
    print(result.stdout)
    
    # 打印命令的标准错误输出（如果有）
    if result.stderr:
        print("Standard Error:")
        print(result.stderr)

if __name__ == '__main__':
    print("Starting Flask server...")
    app.run(debug=True, host='0.0.0.0', port=5000)
    
