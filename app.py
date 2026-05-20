"""
Digital Li Bai — Chat Interface
Usage: python app.py [--port 7860]
Requires: OPENAI_API_KEY and optionally OPENAI_API_BASE (default: https://api.openai.com/v1)
"""

import os
import sys
import argparse
import gradio as gr
from openai import OpenAI

from context_builder import build_context, load_all_poems, load_system_prompt

# --- Config ---
API_KEY = os.getenv("OPENAI_API_KEY", "")
API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
MODEL = os.getenv("MODEL_NAME", "gpt-4o")
MAX_HISTORY = 10

if not API_KEY:
    print("⚠ OPENAI_API_KEY not set. Please set it before starting.")
    print("  Windows: set OPENAI_API_KEY=your-key")
    print("  Linux/Mac: export OPENAI_API_KEY=your-key")
    sys.exit(1)

# --- Init ---
client = OpenAI(api_key=API_KEY, base_url=API_BASE)
poems = load_all_poems()
system_base = load_system_prompt()
print(f"Loaded {len(poems)} poems with dating.")

# --- Chat logic ---


def chat_response(message: str, history: list) -> str:
    """Generate a Li Bai response using OpenAI API with knowledge context."""
    if not message.strip():
        return "……"

    # Build context with knowledge
    context = build_context(message, poems)

    # Build messages from Gradio history (type="messages" format)
    messages = [{"role": "system", "content": context}]
    for msg in history[-(MAX_HISTORY * 2):]:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        messages.append({"role": role, "content": content})

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=0.85,
            max_tokens=2048,
        )
        return response.choices[0].message.content or ""

    except Exception as e:
        error_msg = f"API 调用失败: {e}"
        print(error_msg)
        return f"（李白轻叹一声）此去路远，信使未归……\n\n[技术提示] {error_msg}"


def reset_chat():
    """Clear conversation history."""
    return []


# --- Gradio UI ---

def respond(message, chat_history):
    """Handle a single message turn."""
    if not message:
        return "", chat_history
    reply = chat_response(message, chat_history)
    chat_history.append({"role": "user", "content": message})
    chat_history.append({"role": "assistant", "content": reply})
    return "", chat_history


def create_ui():
    with gr.Blocks(
        title="数字李白",
        theme=gr.themes.Soft(),
    ) as demo:
        gr.Markdown("""
# 数字李白

与诗仙对话，学唐诗，聊人生。

> 基于 LLM Wiki 方法论构建 · 李白存世诗作知识库
        """)

        chatbot = gr.Chatbot(
            label="李白",
            height=500,
            type="messages",
        )

        msg = gr.Textbox(
            label="你说",
            placeholder="比如：教我读《将进酒》 / 你和杜甫怎么认识的？ / 即兴作一首月亮的诗",
        )

        with gr.Row():
            submit_btn = gr.Button("发送", variant="primary")
            clear_btn = gr.Button("清空")

        msg.submit(respond, [msg, chatbot], [msg, chatbot])
        submit_btn.click(respond, [msg, chatbot], [msg, chatbot])
        clear_btn.click(reset_chat, outputs=chatbot)

        gr.Markdown("""
### 试试这样聊
- **教诗**："教我读《将进酒》"
- **论诗**："你的诗有什么特点？"
- **聊人生**："你和杜甫怎么认识的？"
- **即兴创作**："来一首关于月亮的诗"
        """)

    return demo


def main():
    parser = argparse.ArgumentParser(description="数字李白 — 对话原型")
    parser.add_argument("--port", type=int, default=7860, help="Port to run on")
    parser.add_argument("--share", action="store_true", help="Create a public Gradio share link")
    args = parser.parse_args()

    demo = create_ui()
    demo.launch(
        server_port=args.port,
        share=args.share,
        inbrowser=True,
    )


if __name__ == "__main__":
    main()
