import discord
from discord.ext import commands
import random
import asyncio
import os
import json
import math
import re
from gtts import gTTS

from keep import keep_alive

user_money = {}

def load_money_data():
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r") as f:
                return json.load(f)
    except Exception as e:
        print(f"読み込みエラー: {e}")
    return {}

def save_money_data():
    try:
        with open(DATA_FILE, "w") as f:
            json.dump(user_money, f)
    except Exception as e:
        print(f"書き込みエラー: {e}")

DATA_FILE = "user_money.json"



# クライアント作成
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
bot.remove_command('help')
intents.voice_states = True  # VCの入退室を検知するために必須

TEXT_CHANNEL_ID = 1386334847865458688

# 現在のモード（ツン or でれ）
mode = "でれ"

# おみくじの結果
omikuji_results = ["大吉にぇ〜！🌸", "中吉なのら！✨", "小吉にょっす！", "凶…うそでしょ！？💦", "大凶！？なんでやねんっ💢"]

# セリフ集（モード別）
dere_responses = [
    "えへへ、みこがいっちばんかわいいのら！🌸",
    "にぇ〜ん、みこと遊んでくれてありがとだにぇ〜！",
    "みこち参上〜っ！テンションぶち上げだにぇええ！✨",
]
tsun_responses = [
    "べ、別にうれしくなんかないんだからにぇっ…！💢",
    "あんた、ほんっとに構ってほしいのね…しょうがないにぇ〜",
    "はぁ？何言ってんのよ…でゃまれ！///",
]

# あいさつ
greetings = {
    "おはよう": "おはにぇ〜！☀️ 今日も元気にいくにぇー！",
    "おやすみ": "おやすみこ〜！にぇん💤",
    "ただいま": "おかえりにぇ〜！待ってたにぇー🌸",
    "こんにちは": "にゃっはろーー！"
}

#それな
sorena = {
    "それな":"それなにぇ～🌸",
    "🤔":"🤔"
}

# 仕事のリスト（ランダムで選ばれる）
jobs = [
    "ラーメン屋で汗水流して働いた",
    "IT企業でデバッグ地獄を乗り越えた",
    "アイドルのライブスタッフを務めた",
    "深海の宝をサルベージした",
    "宇宙船を修理した",
    "カフェでバリスタとして活躍した",
    "ダンジョンでモンスターを退治した",
    "テーマパークで着ぐるみとして働いた",
    "おばあちゃんの畑を手伝った",
    "秘密のバイトで世界を救った"
]

one_word_phrases = [
    "課題終わったかにぇ？",
    "元気にしてるにぇ？",
    "今日もがんばろうにぇ！",
    "最近どう？",
    "ちゃんと休んでる？",
    "おなかすいた？なんか食べよう。",
    "MGMGやりまっショー",
    "しばくぞ！",
    "今日はもう早く寝ろ！",
    "今週末のデート楽しみだにぇ！"
]

words = [
    "さくら", "みこち", "でんしゃ", "ねこ", "いぬ", "あいす", "たからもの", "がっこう", "えんぴつ", "でんわ",
    "ほしぞら", "おはよう", "こんばんわ", "すいか", "しんかんせん", "こども", "せかい", "らーめん", "たぴおか",
    "かがみ", "てんき", "あめ", "ゆき", "かぜ", "おんがく", "おまつり", "にほん", "とうきょう", "まんが",
    "あそび", "えいが", "ほうせき", "けいたい", "かばん", "くるま", "じてんしゃ", "しごと", "やま", "かわ",
    "うみ", "たいよう", "つき", "ほし", "けしごむ", "おちゃ", "おすし", "ぱんけーき", "ぺんぎん", "うさぎ", "きつね"
]



# ボット起動時に呼ばれるイベント
@bot.event
async def on_ready():
    print(f"✅ 起動完了！{bot.user}としてログイン中だにぇ！")


    is_playing = False

async def play_tts(vc, text):
    global is_playing
    if is_playing:
        return
    is_playing = True

    tts = gTTS(text=text, lang='ja')
    tts.save("tts.mp3")

    audio_source = FFmpegPCMAudio("tts.mp3")
    vc.play(audio_source)

    while vc.is_playing():
        await asyncio.sleep(0.5)

    is_playing = False
    os.remove("tts.mp3")

@bot.event
async def on_voice_state_update(member, before, after):
    # ユーザーがVCに入った時
    if before.channel != after.channel and after.channel is not None:
        vc = member.guild.voice_client
        # BotがまだVCにいなければ入る
        if vc is None:
            try:
                vc = await after.channel.connect()
                print(f"Botが {after.channel} に接続しました")
            except Exception as e:
                print(f"VC接続エラー: {e}")

# メッセージ受信時のイベント
@bot.event
async def on_message(message):
    global mode

    if message.author.bot:
        return
    msg = message.content

    #メンション+一言
    content = message.content.strip()
    if content.endswith("に一言！") and "、" in content:
        name = content.split("、")[0]  # 「、」の前を名前として取得
        reply = f"{name}、何か食べよう"
        await message.channel.send(reply)

    await bot.process_commands(message)
    
    if message.channel.id == TEXT_CHANNEL_ID:
        vc = message.guild.voice_client
        if vc is None:
            # 監視チャンネルからはどのVCに接続すればいいか分からないので
            # 何もしない or メッセージ送信者がVCにいるなら接続などの工夫も可能
            await message.channel.send("Botはどこにも接続していません。")
            return

        await play_tts(vc, message.content)
    

    # あいさつ反応
    for key in greetings:
        if key in msg:
            await message.channel.send(greetings[key])
            return

    for key in sorena:
        if key in msg:
            await message.channel.send(sorena[key])
            return
            
    # 通常会話（「みこ」含む）
    if "みこ" in msg:
        if mode == "ツン":
            reply = random.choice(tsun_responses)
        else:
            reply = random.choice(dere_responses)
        await message.channel.send(reply)
        return

    # モード切替
    if msg.startswith("!モード"):
        if "ツン" in msg:
            mode = "ツン"
            await message.channel.send("ツンモード発動にぇっ！💢")
        elif "でれ" in msg or "デレ" in msg:
            mode = "でれ"
            await message.channel.send("でれモードになったのら〜🌸")
        return
    

# コマンド：!おみくじ
@bot.command()
async def おみくじ(ctx):
    result = random.choice(omikuji_results)
    await ctx.send(f"{ctx.author.mention} の運勢は… {result}")


#働く
@bot.command()
async def 働く(ctx):
    amount = random.randint(1, 100000)
    job = random.choice(jobs)
    user_id = str(ctx.author.id)

    # ユーザーが初めての場合は初期化
    if user_id not in user_money:
        user_money[user_id] = 0

    user_money[user_id] += amount

    await ctx.send(f"{ctx.author.mention} は {job}！\n報酬として 💰 {amount:,} 円 を手に入れた！\n現在の所持金: {user_money[user_id]:,} 円")
    save_money_data()

#所属金
@bot.command()
async def お金(ctx):
    user_id = str(ctx.author.id)
    money = user_money.get(user_id, 0)
    await ctx.send(f"{ctx.author.mention} の現在の所持金は 💰 {money:,} 円 です。")

#あげる
@bot.command()
async def あげる(ctx, member: discord.Member, amount: int):
    giver_id = str(ctx.author.id)
    receiver_id = str(member.id)

    # 自分が初めてなら初期化
    if giver_id not in user_money:
        user_money[giver_id] = 0

    # 相手が初めてなら初期化
    if receiver_id not in user_money:
        user_money[receiver_id] = 0

    # 所持金不足チェック
    if amount <= 0:
        await ctx.send("0円以下は送れません！")
        return
    if user_money[giver_id] < amount:
        await ctx.send("そんなにお金持ってないよ！")
        return

    # お金の移動
    user_money[giver_id] -= amount
    user_money[receiver_id] += amount

    await ctx.send(f"{ctx.author.mention} は {member.mention} に 💸 {amount:,} 円 を渡したよ！\n今の所持金: {user_money[giver_id]:,} 円")
    save_money_data()



# コマンド：!ガチャ
@bot.command()
async def ガチャ(ctx):
    await ctx.send("🎰 ガチャを引くにぇ〜……ドキドキ……💓")
    gifs = [
        "https://media.tenor.com/SdvM8IKHmM8AAAAm/thumbs-up.webp",
        "https://media.tenor.com/rgI-BB8HVT0AAAAM/%E3%81%95%E3%81%8F%E3%82%89%E3%81%BF%E3%81%93-%E3%83%9B%E3%83%AD%E3%83%A9%E3%82%A4%E3%83%96.gif",
        "https://media.tenor.com/QkaBuO9wwo0AAAAM/miko-%E3%81%95%E3%81%8F%E3%82%89%E3%81%BF%E3%81%93.gif",
        "https://media.tenor.com/nf6WBkjapucAAAAM/miko-%E3%81%95%E3%81%8F%E3%82%89%E3%81%BF%E3%81%93.gif",
        "https://media.tenor.com/4b5EuLKAW6wAAAAM/sakura-miko%E3%81%95%E3%81%8F%E3%82%89%E3%81%BF%E3%81%93.gif",
        "https://media.tenor.com/Li-zBSiqfwEAAAAM/miko-%E3%81%95%E3%81%8F%E3%82%89%E3%81%BF%E3%81%93.gif",
        "https://media.tenor.com/w_AhIgqmWe8AAAAM/happy-hololive.gif",
        "https://media.tenor.com/wRSmU-RrF34AAAAM/vtuber-hololive.gif"
    ]
    await ctx.send(random.choice(gifs))



# コマンド：!カウント
count = 1
@bot.command()
async def カウント(ctx):
    global count
    await ctx.send(f"みこちのカウント：{count}回目だにぇ！")
    count += 1

# コマンド：!タイマー
@bot.command()
async def タイマー(ctx, minutes: int):
    await ctx.send(f"{minutes}分のタイマー開始だにぇ〜💦")
    await asyncio.sleep(minutes * 60)
    await ctx.send(f"{minutes}分たったにぇ〜！お疲れ様だにぇ🌸")


@bot.command()
async def 草(ctx):
    kusa = [
        "草ｗｗｗ。大爆笑だにぇー",
        "（笑）",
        "( ´∀｀ )面白いにぇね。",
        "草ｗ。大草原不可避だにぇー",
    ]
    await ctx.send(random.choice(kusa))

# コマンド：!うた
@bot.command()
async def うた(ctx):
    lyrics = [
        "箱にあたる日を　横眼で眺めて。そっと陰る木の根に一人で比べていた―。（サクラカゼ）",
        "夢って何だろう。うまく言えない私へ。歌っていいんだよ。まぶしい光の中で。（flower rhapsody)✨",
        "きゅんきゅんみこきゅんきゅん",
        "ねえ思い出したんだ。そっと涙した日を。さあ数えてみようか　これまで起こした奇跡を。（アワーツリー)"
    ]
    await ctx.send(random.choice(lyrics))

# コマンド: !すうあて
@bot.command()
async def すうあて(ctx):
    number = random.randint(1, 100)
    await ctx.send("にぇ〜！1から100の数字を当ててみてほしいのら！")

    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel and m.content.isdigit()

    for _ in range(5):
        try:
            guess_msg = await bot.wait_for("message", timeout=15.0, check=check)
            guess = int(guess_msg.content)
            if guess < number:
                await ctx.send("もっと大きいのにぇ〜！")
            elif guess > number:
                await ctx.send("もっと小さいのら！")
            else:
                await ctx.send("あたりにぇ〜！🎯すごいにぇ！")
                return
        except asyncio.TimeoutError:
            await ctx.send("にぇぇぇ…時間切れだにぇ💦")
            return
    await ctx.send(f"残念…正解は {number} だったにぇ〜😿")

# コマンド: !じゃんけん

@bot.command()
async def じゃんけん(ctx, user_hand: str):
    choices = ["ぐー", "ちょき", "ぱー"]
    bot_hand = random.choice(choices)
    win = {
        ("ぐー", "ちょき"),
        ("ちょき", "ぱー"),
        ("ぱー", "ぐー")
    }

    if user_hand not in choices:
        await ctx.send("にぇ？『ぐー』『ちょき』『ぱー』から選ぶのら！")
        return

    result = "引き分けだにぇ〜！"
    if (user_hand, bot_hand) in win:
        result = "みこちの負けにぇ〜😭おめでとう！"
    elif user_hand != bot_hand:
        result = "みこちの勝ちにぇっ！💪🌸"

    await ctx.send(f"{ctx.author.mention} vs みこち\nあなた：{user_hand} / みこ：{bot_hand}\n{result}")

# コマンド: !ルーレット
@bot.command()
async def ルーレット(ctx):
    items = ["🍓いちご", "🎤みこの歌", "💣爆発", "🌸愛情", "🎁シークレット"]
    result = random.choice(items)
    await ctx.send(f"ぐるぐるぐる…🎰 結果は… {result} だったにぇ〜！")

# 単語当てゲーム
@bot.command()
async def たんごあて(ctx):
    word = random.choice(words)
    guessed = ["●"] * len(word)
    attempts = 7
    guessed_letters = set()

    await ctx.send(f"🌸 単語当てゲームスタートにぇ！\n{''.join(guessed)}\nひらがな一文字ずつ当ててにぇ！ 残り{attempts}回！")

    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel and len(m.content) == 1

    while attempts > 0:
        try:
            guess_msg = await bot.wait_for("message", timeout=30.0, check=check)
            guess = guess_msg.content

            if guess in guessed_letters:
                await ctx.send("その文字はもう使ってるにぇ〜！")
                continue

            guessed_letters.add(guess)

            if guess in word:
                for i, char in enumerate(word):
                    if char == guess:
                        guessed[i] = guess
                await ctx.send(f"当たりにぇ！\n{''.join(guessed)}")
            else:
                attempts -= 1
                await ctx.send(f"はずれにぇ…残り{attempts}回だにぇ〜！\n{''.join(guessed)}")

            if "●" not in guessed:
                await ctx.send(f"🎉 正解にぇ〜！単語は「{word}」だったにぇ！")
                return
        except asyncio.TimeoutError:
            await ctx.send("にぇぇ…時間切れだにぇ💦")
            return

    await ctx.send(f"残念…単語は「{word}」だったにぇ😿 またチャレンジしてにぇ！")


# 音声チャンネルに参加するコマンド：!join
@bot.command()
async def join(ctx):
    if ctx.author.voice is None:
        await ctx.send("にぇぇ… まずあなたがボイスチャンネルに入っててほしいにぇ！💦")
        return

    if ctx.author.voice:
        channel = ctx.author.voice.channel
        await channel.connect()
        await ctx.send(f"みこち、{channel} に参加したのら〜！")
    else:
        await ctx.send("まずはボイスチャンネルに入ってね！にぇ〜！")

# 音声チャンネルから抜けるコマンド：!leave
@bot.command()
async def leave(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("みこち、ボイスチャンネルから出るにぇ！")
    else:
        await ctx.send("ボイスチャンネルにいないにぇ〜！")


@bot.command()
async def けいさん(ctx, *, expression: str):
    try:
        # 安全な式評価
        allowed_names = {
            k: v for k, v in math.__dict__.items() if not k.startswith("__")
        }
        result = eval(expression, {"__builtins__": None}, allowed_names)
        await ctx.send(f"📐 計算結果は：`{result}` にぇ〜！")
    except Exception as e:
        await ctx.send(f"⚠️ 計算できなかったにぇ…エラー：{e}")


    #保存

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("引数が足りないにぇ！ちゃんと入力してにぇ〜。")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("引数の形式が正しくないにぇ！もう一度確認してにぇ。")
    elif isinstance(error, commands.CommandNotFound):
        # 存在しないコマンドに対しては無視しても良いし、通知するかはお好みで
        pass
    else:
        # 予期しないエラーは詳細をログに出しつつユーザーには簡単なメッセージ
        print(f"エラー発生: {error}")
        await ctx.send(f"ごめんにぇ、何か問題が発生したにぇ…😿")



# ヘルプコマンドの追加
@bot.command()
async def 助けて(ctx):
    help_message = """
**🌸 最強みこBotの使い方リスト 🌸**

**🎲 基本コマンド**
`!おみくじ` - みこちがおみくじを引いてくれるにぇ〜  
`!ガチャ` - ランダムでGIF画像をゲット！  
`!カウント` - カウントしてくにぇ〜！  
`!タイマー [分]` - タイマーをセットするよ！

**🎮 ミニゲーム**
`!すうあて` - 数当てゲーム（1〜100）をしよう！  
`!じゃんけん [ぐー/ちょき/ぱー]` - みことじゃんけん勝負だにぇ〜  
`!ルーレット` - 運試しルーレット！

**💬 特殊リアクション**
「おはよう」「おやすみ」「ただいま」→ 自動で返事するにぇ！  
「それな」「🤔」→ 特別リアクションもあるよ！

**💰 お金機能**
`!働く` - お金を稼ぐにぇ！  
`!お金` - 自分の所持金を見るにぇ  
`!あげる @ユーザー 金額` - お金を他の人にあげるにぇ〜！

**🎧 音声チャンネル**
`!join` - みこちがVCに参加するにぇ！  
`!leave` - VCから退出するにぇ〜！

**🧮 計算機**
`!けいさん 式` - 数式を計算してくれるにぇ！例：`!けいさん 3 + 4 * 2`

**🎤 ゆうたに一言 / うた / 草**
`!ゆったに一言` - ゆうたへの特別な一言  
`!うた` - みこの歌詞が届くかも？  
`!草` - 面白いときに押してね！

**🌀 モード切り替え**
`!モード ツン` または `!モード でれ` - みこちの性格が変わるにぇ！

----
にぇ〜！どんどん使って、みこといっぱい遊んでにぇ🌸
"""
    await ctx.send(help_message)

# 最後にここでBot起動
user_money = load_money_data()
keep_alive()
bot.run(os.environ['TOKEN'])