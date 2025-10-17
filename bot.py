import telebot
import os
import tempfile

# Replace with your bot token from BotFather
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"

bot = telebot.TeleBot(BOT_TOKEN)

# Store file references temporarily
user_files = {}

@bot.message_handler(commands=['start'])
def start_command(message):
    bot.reply_to(message, "👋 Hello! Main text file split bot hoon.

📄 Mujhe ek text file bhejo
✂️ Phir /spl <number> command se reply karo

Example: /spl 10")

@bot.message_handler(commands=['help'])
def help_command(message):
    help_text = """
🤖 **Bot Usage:**

1️⃣ Mujhe ek text file bhejo (.txt file)
2️⃣ Us file ko reply karte hue command bhejo: /spl <number>
3️⃣ Main tumhe split files bhej dunga

**Example:**
- /spl 10 → Har file me 10 lines
- /spl 20 → Har file me 20 lines
- /spl 50 → Har file me 50 lines

**Note:** File ko reply karna zaroori hai!
    """
    bot.reply_to(message, help_text)

@bot.message_handler(content_types=['document'])
def handle_document(message):
    try:
        # Get file info
        file_info = bot.get_file(message.document.file_id)
        file_name = message.document.file_name
        
        # Check if it's a text file
        if not file_name.endswith('.txt'):
            bot.reply_to(message, "⚠️ Sirf .txt files support karti hoon!")
            return
        
        # Store file info for this user
        user_files[message.from_user.id] = {
            'file_id': message.document.file_id,
            'file_info': file_info,
            'file_name': file_name,
            'message_id': message.message_id
        }
        
        bot.reply_to(message, f"✅ File received: {file_name}

Ab is message ko reply karte hue /spl <number> command bhejo.

Example: /spl 10")
        
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

@bot.message_handler(commands=['spl'])
def split_command(message):
    try:
        # Check if command has a number
        command_parts = message.text.split()
        if len(command_parts) < 2:
            bot.reply_to(message, "⚠️ Please provide split amount!

Example: /spl 10")
            return
        
        try:
            split_amount = int(command_parts[1])
            if split_amount <= 0:
                raise ValueError
        except ValueError:
            bot.reply_to(message, "⚠️ Valid number provide karo!

Example: /spl 10")
            return
        
        # Check if this is a reply to a document
        if not message.reply_to_message or message.reply_to_message.content_type != 'document':
            bot.reply_to(message, "⚠️ Pehle text file bhejo, phir us file ko reply karte hue /spl command use karo!")
            return
        
        user_id = message.from_user.id
        
        # Check if we have file info
        if user_id not in user_files:
            bot.reply_to(message, "⚠️ File nahi mili! Pehle file bhejo.")
            return
        
        # Send processing message
        processing_msg = bot.reply_to(message, "⏳ Processing your file...")
        
        file_data = user_files[user_id]
        file_info = file_data['file_info']
        
        # Download the file
        downloaded_file = bot.download_file(file_info.file_path)
        
        # Create temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            # Save downloaded file
            temp_file_path = os.path.join(temp_dir, 'original.txt')
            with open(temp_file_path, 'wb') as f:
                f.write(downloaded_file)
            
            # Read all lines
            with open(temp_file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            total_lines = len(lines)
            
            # Calculate number of split files needed
            num_files = (total_lines + split_amount - 1) // split_amount
            
            bot.edit_message_text(
                f"📊 Total Lines: {total_lines}
✂️ Split Amount: {split_amount}
📁 Files to create: {num_files}

⏳ Creating files...",
                message.chat.id,
                processing_msg.message_id
            )
            
            # Split and send files
            for i in range(num_files):
                start_idx = i * split_amount
                end_idx = min((i + 1) * split_amount, total_lines)
                
                # Get lines for this split
                split_lines = lines[start_idx:end_idx]
                
                # Create split file
                split_file_name = f"split{i+1}.txt"
                split_file_path = os.path.join(temp_dir, split_file_name)
                
                with open(split_file_path, 'w', encoding='utf-8') as f:
                    f.writelines(split_lines)
                
                # Send the split file
                with open(split_file_path, 'rb') as f:
                    bot.send_document(
                        message.chat.id,
                        f,
                        caption=f"📄 {split_file_name}
📊 Lines: {len(split_lines)}"
                    )
            
            # Delete processing message and send completion message
            bot.delete_message(message.chat.id, processing_msg.message_id)
            bot.reply_to(message, f"✅ Done! {num_files} files sent successfully!")
        
        # Clean up stored file info
        del user_files[user_id]
        
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(message, "ℹ️ Main sirf text files split kar sakta hoon.

📄 File bhejo aur /spl command use karo!
/help ke liye help dekho.")

# Start bot
print("🤖 Bot is running...")
bot.infinity_polling()
