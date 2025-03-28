from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters
from PIL import Image, ImageDraw, ImageFont
import io

# ======= DIP Image Generator (Final Version) =======
def generate_dip_image(binary_str: str) -> Image.Image:
    num_switches = len(binary_str)
    switch_width = 32
    switch_height = 80
    spacing = 6
    margin = 20

    total_width = num_switches * (switch_width + spacing) + margin * 2 - spacing
    total_height = switch_height + 80

    img = Image.new("RGB", (total_width, total_height), color="white")
    draw = ImageDraw.Draw(img)

    # Red background panel with black border
    dip_top = 50
    dip_bottom = dip_top + switch_height
    panel_rect = [margin - 10, dip_top - 30, total_width - margin + 10, dip_bottom + 30]
    draw.rectangle(panel_rect, fill="#cc0000", outline="black", width=2)

    # Font setup
    try:
        font = ImageFont.truetype("arial.ttf", 14)
        font_bold = ImageFont.truetype("arialbd.ttf", 16)
    except IOError:
        font = ImageFont.load_default()
        font_bold = ImageFont.load_default()

    # ON label (white)
    draw.text((margin, dip_top - 25), "ON", fill="white", font=font_bold)

    for i, bit in enumerate(binary_str):
        x = margin + i * (switch_width + 6)
        y = dip_top

        # DIP switch slot (frame)
        draw.rectangle([x, y, x + switch_width, y + switch_height], outline="black", width=2)

        if bit == '1':
            # ON: white bottom
            draw.rectangle([x + 2, y + switch_height // 2, x + switch_width - 2, y + switch_height - 2], fill="white")
            draw.rectangle([x + 2, y + 2, x + switch_width - 2, y + switch_height // 2], fill="#cc0000")
        else:
            # OFF: white top
            draw.rectangle([x + 2, y + 2, x + switch_width - 2, y + switch_height // 2], fill="white")
            draw.rectangle([x + 2, y + switch_height // 2, x + switch_width - 2, y + switch_height - 2], fill="#cc0000")

        # Switch number (white)
        label_x = x + switch_width // 2 - 5
        label_y = y + switch_height + 5
        draw.text((label_x, label_y), str(i + 1), fill="white", font=font)

    return img

# ======= Language Setup =======
LANG_TEXTS = {
    "ua": {
        "choose_bits": "Оберіть кількість бітів:",
        "send_number": "Надішліть число адреси, і я згенерую DIP Switch."
    },
    "cz": {
        "choose_bits": "Zvolte počet bitů:",
        "send_number": "Pošlete mi číslo adresy a vygeneruji DIP Switch."
    }
}

# ======= Handlers =======
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "lang" in context.user_data:
        await show_bit_options(update, context)
        return

    keyboard = [
        [InlineKeyboardButton("Українська 🇺🇦", callback_data="lang_ua"),
         InlineKeyboardButton("Čeština 🇨🇿", callback_data="lang_cz")]
    ]
    await update.message.reply_text("Виберіть мову / Zvolte jazyk:",
                                    reply_markup=InlineKeyboardMarkup(keyboard))

async def language_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = query.data.split("_")[1]
    context.user_data["lang"] = lang
    await show_bit_options(update, context, edit=True)

async def show_bit_options(update: Update, context: ContextTypes.DEFAULT_TYPE, edit=False):
    lang = context.user_data.get("lang", "ua")
    keyboard = [
        [InlineKeyboardButton("6", callback_data="bits_6"),
         InlineKeyboardButton("8", callback_data="bits_8"),
         InlineKeyboardButton("10", callback_data="bits_10"),
         InlineKeyboardButton("12", callback_data="bits_12")]
    ]
    text = LANG_TEXTS[lang]["choose_bits"]
    markup = InlineKeyboardMarkup(keyboard)

    if edit:
        await update.callback_query.edit_message_text(text=text, reply_markup=markup)
    else:
        await update.message.reply_text(text, reply_markup=markup)

async def bits_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    bits = int(query.data.split("_")[1])
    context.user_data["bits"] = bits
    lang = context.user_data.get("lang", "ua")
    await query.edit_message_text(LANG_TEXTS[lang]["send_number"])

async def handle_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        address = int(update.message.text.strip())
        bits = context.user_data.get("bits", 8)
        binary = format(address, f"0{bits}b")[::-1]
        image = generate_dip_image(binary)

        with io.BytesIO() as output:
            image.save(output, format="PNG")
            output.seek(0)
            await update.message.reply_photo(photo=output)
    except:
        await update.message.reply_text("Будь ласка, введіть правильне число / Zadejte platné číslo.")

# ======= Main =======
def main():
    import os
    TOKEN = os.getenv("TOKEN")
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(language_selected, pattern="^lang_"))
    app.add_handler(CallbackQueryHandler(bits_selected, pattern="^bits_"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_number))

    app.run_polling()

if __name__ == "__main__":
    main()
