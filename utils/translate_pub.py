import aiohttp
import asyncio
import datetime
import json
import os
import requests
from typing import Optional,Tuple
import config   # config.py から読み込む：相対パスのためエラーとなる可能性がある

DEFAULT_COUNT_DATA = {"count": 0, "month": "YYYY-MM"}

class Translator:
    """
    DeepL APIを使用してテキスト翻訳を行うクラス。
    APIキーと文字数カウント用のファイルパスを管理します。
    """
    def __init__(self, api_key: Optional[str] = None, char_count_file: str = config.CHAR_COUNT_FILE):
        """
        Translatorクラスのインスタンスを初期化します。

        Parameters:
        ----------
        api_key : Optional[str]
            DeepLのAPIキー。指定しない場合は config.DEEPL_API_KEY を参照します。
        char_count_file : str
            文字数カウントを保存するJSONファイルのパス。
        """
        self.api_key = api_key or config.DEEPL_API_KEY
        self.char_count_file = char_count_file

        # dataディレクトリが存在しない場合に作成
        dir_path = os.path.dirname(self.char_count_file)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)

        # 文字数カウントファイルの初期化
        if not os.path.exists(self.char_count_file):
            self.check_deepl_count()

        return


    def _set_char_count_file(self) -> None:
        """
        文字数カウントファイルの有無をチェックし、存在しない場合はファイルを作成する。

        """
        # dataディレクトリが存在しない場合に作成
        dir_path = os.path.dirname(self.char_count_file)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)

        # 文字数カウントファイルの初期化
        if not os.path.exists(self.char_count_file):
            self.check_deepl_count()

        return


    def get_char_count(self) -> dict[int, str]:
        """
        現在の月の翻訳文字数を取得します。

        Returns:
        -------
        count_data : dict
            合計翻訳文字数と現在の月"YYYY-MM"の辞書。
        """
        # 現在月を取得し、初期値作成
        current_month = datetime.datetime.now().strftime("%Y-%m")
        count_data = DEFAULT_COUNT_DATA
        count_data["month"] = current_month

        if os.path.exists(self.char_count_file):
            try:
                with open(self.char_count_file, "r", encoding="utf-8") as f:
                    file_data = json.load(f)
                # 月が同じであれば、そのデータを使用
                if file_data.get("month") == current_month:
                    count_data = file_data
            except (json.JSONDecodeError, FileNotFoundError, TypeError):
                pass
        else:
            self.check_deepl_count()
        
        return count_data


    def update_char_count(self, add_count: int) -> None:
        """
        文字数カウントファイルを更新します。同じ月の場合はカウントを追加します。

        Parameters:
        ----------
        add_count : int
            追加する翻訳文字数
        """
        current_month = datetime.datetime.now().strftime("%Y-%m")
        data_after = DEFAULT_COUNT_DATA
        data_after["month"] = current_month

        # 更新前のデータを取得
        data_before = self.get_char_count()
        # 同じ月であればカウントを追加
        if data_before.get("month") == current_month:
            data_after["count"] = data_before.get("count") + add_count

        with open(self.char_count_file, "w", encoding="utf-8") as f:
            json.dump(data_after, f, ensure_ascii=False, indent=2)

        return


    def check_deepl_count(self) -> None:
        """
        DEEPL上の文字数制限を取得し、文字数カウントファイルを作成します。。

        """
        # 初期化
        count = 0
        limit = config.CHAR_LIMIT

        # 使用量取得APIを実行
        try:
            api_params = {"auth_key": self.api_key}
            res = requests.get(config.DEEPL_USAGE_URL, params=api_params, timeout=10)
            res.raise_for_status() # HTTPエラーがあれば例外を発生させる
            data = res.json()
            count = data.get("character_count", 0)
            limit = data.get("character_limit", config.CHAR_LIMIT) # configから参照
        except requests.exceptions.RequestException as e:
            print(f"DeepL API接続エラー: {e}")
        except json.JSONDecodeError as e:
            print(f"DeepL API JSON解析エラー: {e}")
        except Exception as e:
            print(f"DeepL APIその他エラー: {e}")

        # 文字数カウントファイルを更新
        current_month = datetime.datetime.now().strftime("%Y-%m")
        data_count = DEFAULT_COUNT_DATA
        data_count["month"] = current_month
        data_count["count"] = count
        with open(self.char_count_file, "w", encoding="utf-8") as f:
            json.dump(data_count, f, ensure_ascii=False, indent=2)

        return


    async def translate(self, original_text: str, target_lang: str = config.DEFAULT_LANG) -> tuple[str, str]:
        """
        指定されたテキストをターゲット言語に翻訳します。

        Parameters:
        ----------
        original_text : str
            翻訳する元テキスト。
        target_lang : str
            翻訳先の言語コード (例: "EN", "JA")。

        Returns:
        ----------
        return_text : str
            翻訳されたテキスト。エラーの場合は "[翻訳エラー]" を返します。
        return_lang : str
            翻訳元言語。エラーの場合は "ERROR" を返します。
        """
        return_text = "[翻訳エラー]"
        return_lang = "ERROR"

        if not self.api_key:
            return return_text, return_lang

        params = {
            "auth_key": self.api_key,
            "text": original_text,
            "target_lang": target_lang
        }

        # DEEPL_API実行
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(config.DEEPL_API_URL, data=params) as resp: # config.py から読み込む
                    if resp.status == 200:
                        res_json = await resp.json()
                        return_text = res_json["translations"][0]["text"]
                        return_lang = res_json["translations"][0]["detected_source_language"]
                        # 文字数カウントファイルを更新
                        self.update_char_count(len(original_text))
                    else:
                        error_text = await resp.text()
                        return_text = f"[翻訳エラー]: {resp.status} : {error_text}"

        except aiohttp.ClientError as err:
            # print(f"AIOHTTP Client Error: {err}")
            return_text = "[翻訳エラー]: 接続に失敗しました"

        # print(f"翻訳結果: {return_text} , 翻訳元言語: {return_lang}")
        return return_text, return_lang


# --- 以下はクラスの使用方法のサンプルです ---
# --- config.pyが相対インポートになるため、直接実行できません ---
async def main():
    deepl_api_key = "XXXXXXXXXXXXXXXXXXXXX"
    path_count_file = os.path.dirname(__file__) + "/discord-translator-bot/data/char_count.json"
    # インスタンスを作成
    translator = Translator()

    # インスタンスを作成(API_KEYを指定する場合)
    # translator = Translator(api_key=deepl_api_key, char_count_file=path_count_file)

    original_text = "Hello, world!"
    source_lang = ""

    # 現在のカウントを取得
    initial_count_json = translator.get_char_count()
    print(f"翻訳前の文字数カウント: {initial_count_json}")

    # 翻訳を実行
    translated_text, source_lang = await translator.translate(original_text, "JA")
    print(f"翻訳結果: {translated_text} , 翻訳元言語: {source_lang}")

    # 翻訳後のカウントを取得
    updated_count_json = translator.get_char_count()
    print(f"翻訳後の文字数カウント: {updated_count_json} , 追加文字数: {len(original_text)}")

    '''
    # 別の言語へ
    translated_text, source_lang = await translator.translate(original_text, "JA")
    print(f"翻訳結果: {translated_text} , 翻訳元言語: {source_lang}")

    # 最終カウントを取得
    final_count_json = translator.get_char_count()
    print(f"最終的な文字数カウント: {final_count_json}")
    '''
    return


if __name__ == '__main__':
    asyncio.run(main())
