
import streamlit as st
import openai
import urllib.parse

# OpenAI APIキーの取得（Secretsに登録されているキーを読み取る）
try:
    if "openai_api_key" in st.secrets:
        openai_api_key = st.secrets["openai_api_key"]
    elif "openai" in st.secrets and "openai_api_key" in st.secrets["openai"]:
        openai_api_key = st.secrets["openai"]["openai_api_key"]
    else:
        raise KeyError("OpenAI APIキーが見つかりません。StreamlitのSecretsに設定してください。")
except KeyError as e:
    st.error(f"❌ {e}")
    st.stop()

# OpenAI クライアントの初期化（修正済み）
openai.api_key = openai_api_key

# 診断の質問
questions = [
    {"text": "Q1. あなたの性別を選んでください", "choices": ["男性", "女性"]},
    {"text": "Q2. あなたの顔の印象に近いのは？", "choices": ["丸みがあり、やわらかい", "直線的でシャープ", "スッキリと縦長"]},
    {"text": "Q3. あなたの理想の雰囲気は？", "choices": ["知的で洗練された", "親しみやすい", "個性的でおしゃれ"]},
    {"text": "Q4. あなたのファッションスタイルは？", "choices": ["シンプルで洗練", "ナチュラルでリラックス", "トレンド重視"]},
    {"text": "Q5. 眼鏡を使うシーンは？", "choices": ["ビジネス・フォーマル", "日常使い", "おしゃれアイテム"]},
]

# `st.session_state` の初期化
st.session_state.setdefault("current_question", 0)
st.session_state.setdefault("answers", [])
st.session_state.setdefault("submitted", False)
st.session_state.setdefault("image_url", None)
st.session_state.setdefault("result", "")

# 診断結果の生成（250文字以内）
def generate_result():
    gender = st.session_state["answers"][0]  # 性別取得
    answers_text = "\n".join([f"{q['text']} {a}" for q, a in zip(questions[1:], st.session_state["answers"][1:])])

    prompt = f"""
    You are a professional eyewear designer. 
    Based on the user's answers, create a compelling and artistic recommendation for their perfect glasses.
    **Provide the response in Japanese within 250 characters.**

    User's gender: {gender}
    User's responses:
    {answers_text}

    Response format:
    -------------
    あなたにおすすめの眼鏡は【〇〇】です！
    （250文字以内で、眼鏡のデザインの魅力、特徴、かけたときの印象を簡潔に表現）
    -------------
    """

    response = openai.ChatCompletion.create(
        model="gpt-4-turbo",
        messages=[{"role": "system", "content": prompt}],
        temperature=0.7
    )

    return response["choices"][0]["message"]["content"], gender

# 眼鏡デザインの画像を DALL·E で生成
def generate_glasses_image(description, gender):
    image_prompt = f"""
    A single stylish eyeglass: {description}. 
    Designed specifically for a {gender}.
    The eyeglasses should be the only object in the image, centered, with a plain, solid-colored background.
    No additional elements like text, labels, color variations, decorations, faces, or accessories.
    """

    response = openai.Image.create(
        model="dall-e-3",
        prompt=image_prompt,
        n=1,
        size="1024x1024"
    )

    return response["data"][0]["url"]

# タイトル表示
st.title("👓 眼鏡デザイン診断")
st.write("あなたにぴったりの眼鏡デザインを診断します！")

# 質問の表示
if st.session_state["current_question"] < len(questions):
    q = questions[st.session_state["current_question"]]
    st.subheader(q["text"])

    for choice in q["choices"]:
        if st.button(choice):
            st.session_state["answers"].append(choice)
            st.session_state["current_question"] += 1

            if st.session_state["current_question"] == len(questions):
                st.session_state["submitted"] = True

            st.experimental_rerun()

# 診断するボタンの表示
if st.session_state["submitted"] and not st.session_state["result"]:
    st.subheader("🎯 すべての質問に答えました！")
    if st.button("🔍 診断する"):
        result, gender = generate_result()
        st.session_state["result"] = result

        try:
            recommended_glasses = result.split("あなたにおすすめの眼鏡は【")[1].split("】です！")[0]
        except IndexError:
            recommended_glasses = "classic round metal frame glasses"

        st.session_state["image_url"] = generate_glasses_image(recommended_glasses, gender)

        st.experimental_rerun()

# 診断結果の表示
if st.session_state["result"]:
    st.subheader("🔮 診断結果")
    st.write(st.session_state["result"])

    if st.session_state["image_url"]:
        st.image(st.session_state["image_url"], caption="あなたにおすすめの眼鏡デザイン", use_column_width=True)

    # LINE共有ボタン
    share_text = urllib.parse.quote(f"👓 診断結果: {st.session_state['result']}")
    share_url = f"https://social-plugins.line.me/lineit/share?text={share_text}"
    st.markdown(f"[📲 LINEで友達に共有する]({share_url})", unsafe_allow_html=True)
