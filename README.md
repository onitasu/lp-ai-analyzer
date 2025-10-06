# 🎨 AI-Powered Landing Page Analyzer

ジャンル別に最適化されたLPの視覚改善提案アプリ

## 🚀 クイックスタート

### 1. インストール

```bash
pip install -r requirements.txt
```

### 2. 環境変数の設定

```bash
# Geminiを使用する場合
export GEMINI_API_KEY="your-gemini-api-key"

# OpenAIを使用する場合
export OPENAI_API_KEY="your-openai-api-key"
```

### 3. アプリの起動

```bash
streamlit run app.py
```

ブラウザで自動的に開きます：`http://localhost:8501`

---

## 📝 使い方

### Step 1: LPの種類を選択

サイドバーで、分析するLPの種類を選択：
- 🚀 **SaaS・ツール系**
- 🛒 **D2C・物販系**
- 📚 **教育・講座系**
- 👥 **採用・求人系**
- 📱 **アプリダウンロード系**

### Step 2: URLを入力

分析したいLPのURLを入力します。

### Step 3: 解析実行

「🚀 解析する」ボタンをクリックすると、選択したジャンルに最適化されたプロンプトで分析が実行されます。

---

## 🎯 機能

- **ジャンル別最適化**: 5つのLPジャンルに対応した専用プロンプト
- **視覚改善提案**: デザイン・レイアウト・色彩などの視覚的な改善点を抽出
- **問題点の検出**: LPの問題点を優先度付きで表示
- **改善提案**: 具体的な改善案を提示
- **結果のエクスポート**: JSON形式でダウンロード可能

---

## 🎛️ 詳細設定

### モデルの選択

- **Google Gemini**:
  - `gemini-2.5-flash` - 高速・低コスト（推奨）
  - `gemini-2.5-pro` - 高品質・高コスト

- **OpenAI GPT-5**:
  - `gpt-5` - 最高品質（複雑な推論）
  - `gpt-5-mini` - コスト最適化（バランス型）
  - `gpt-5-nano` - 高速処理（シンプルなタスク）

### Verbosity（出力の詳細度）

- `low` - 簡潔な出力
- `medium` - 標準的な詳細度
- `high` - 詳細な説明

### Reasoning Effort（推論の深さ）

- `minimal` - 最速（最小限の推論）
- `low` - 高速（軽い推論）
- `medium` - 標準（バランス型）
- `high` - 最高品質（深い推論）

**注意**: OpenAI GPT-5では、これらは正式なAPIパラメータです。Geminiでは、プロンプト指示として追加されます。

---

## 📁 プロジェクト構成

```
lp-ai-1759595228/
├── app.py                    # メインアプリケーション
├── requirements.txt          # 依存パッケージ
├── packages.txt             # システムパッケージ
├── README.md                # このファイル
└── src/
    ├── capture/             # Webページキャプチャ
    │   ├── browser_utils.py
    │   └── web_capture.py
    ├── llm/                 # LLM関連
    │   ├── exceptions.py
    │   ├── gemini_client.py
    │   ├── openai_client.py
    │   ├── pipeline.py
    │   ├── prompts.py
    │   ├── schemas.py
    │   └── genre_prompts.py  # ジャンル別プロンプト
    ├── preview/             # プレビュー生成
    │   └── preview.py
    └── utils/               # ユーティリティ
        ├── io.py
        ├── json_tools.py
        └── run_logger.py
```

---

## 🔧 トラブルシューティング

### サイドバーが表示されない

- ブラウザの幅を広げてください
- または、左上の「>」アイコンをクリックしてサイドバーを展開

### API エラーが発生する

- 環境変数（`GEMINI_API_KEY`または`OPENAI_API_KEY`）が正しく設定されているか確認
- APIキーが有効か確認
- APIの利用制限に達していないか確認

### スクリーンショットが取得できない

- URLが正しいか確認
- Webページがアクセス可能か確認
- プライベートページの場合は、公開設定を確認

---

## 💡 推奨設定

### 高速・低コスト向け
```
Model: gemini-2.5-flash または gpt-5-mini
Verbosity: low
Reasoning: minimal
```

### 高品質向け
```
Model: gemini-2.5-pro または gpt-5
Verbosity: medium
Reasoning: high
```

---

## 📄 ライセンス

このプロジェクトはMITライセンスの下で公開されています。

---

## 🙏 クレジット

- **Streamlit** - UIフレームワーク
- **Google Gemini** - AIモデル
- **OpenAI GPT-5** - AIモデル
- **Playwright** - Webページキャプチャ

---

## 📞 サポート

問題が発生した場合は、GitHubのIssuesでお知らせください。
