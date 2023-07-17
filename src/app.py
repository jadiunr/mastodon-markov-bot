#!/usr/bin/env python3
import yaml
import time
import threading
import mastodonTool
import discordTool
import os
import datetime
import markovify
import exportModel
import re

# 設定の読み込み
with open('config.yml') as yml:
    config = yaml.safe_load(yml)

def worker():
    # 学習
    reads = config['reads']
    for read in reads:
        domain = read['domain']
        acct = read['acct']
        account_id = read['account_id']
        read_access_token = read['access_token']
        # write_access_token = config['write']['access_token']
        account_info = mastodonTool.get_account_info(domain, account_id, read_access_token)
        params = {"exclude_replies": 0, "exclude_reblogs": 1}
        filename = acct
        filepath = os.path.join("./chainfiles", os.path.basename(filename.lower()) + ".json")
        if (os.path.isfile(filepath) and datetime.datetime.now().timestamp() - os.path.getmtime(filepath) < 60 * 60 * 24):
            print("モデルは再生成されません")
        else:
            exportModel.generateAndExport(mastodonTool.loadMastodonAPI(domain, read_access_token, account_info['id'], params), filepath)
            print("LOG,GENMODEL," + str(datetime.datetime.now()) + "," + account_info["username"].lower())   # Log
    
    # 生成
    for write in config['writes']:
        combinedTextModel = None
        for read_acct in write['read_accts']:
            with open("./chainfiles/{}.json".format(read_acct.lower())) as f:
                textModel = markovify.Text.from_json(f.read())
                combinedTextModel = textModel if combinedTextModel is None else markovify.combine([combinedTextModel, textModel])
        sentence = combinedTextModel.make_sentence(tries=300)
        sentence = "".join(sentence.split()) + ' #bot'
        sentence = re.sub(r'(:.*?:)', r' \1 ', sentence)
        print(sentence)
        try:
            if ('discord' in write):
                discordTool.post(write['discord']['webhook_url'], sentence)
            if ('mastodon' in write):
                mastodonTool.post_toot(write['mastodon']['domain'], write['mastodon']['access_token'], {"status": sentence})
        except Exception as e:
            print("投稿エラー: {}".format(e))

def schedule(f, interval=1200, wait=True):
    base_time = time.time()
    next_time = 0
    while True:
        t = threading.Thread(target=f)
        t.start()
        if wait:
            t.join()
        next_time = ((base_time - time.time()) % interval) or interval
        time.sleep(next_time)


if __name__ == "__main__":
    # 定期実行部分
    schedule(worker)
    # worker()
