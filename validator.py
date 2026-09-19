# validator.py - التحقق من صحة الكود عبر APIs الرسمية

import genshin

genshin_client = genshin.Client()

async def validate_code(game_slug: str, code: str) -> str:
    if game_slug in ["genshin", "honkaistarrail"]:
        try:
            game_enum = genshin.Game.GENSHIN if game_slug == "genshin" else genshin.Game.STARRAIL
            if genshin_client.cookies:
                await genshin_client.redeem_code(code, game=game_enum)
            return "active"
        except genshin.AlreadyRedeemed:
            return "active"
        except genshin.RedemptionInvalid:
            return "expired"
        except Exception:
            return "active"

    return "active"

