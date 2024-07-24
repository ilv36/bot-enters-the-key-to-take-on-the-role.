import nextcord
from nextcord.ext import commands
from nextcord.ui import Button, View, Modal, TextInput
import json
import random
import string
from nextcord import Interaction
import datetime

# สร้าง intents เพื่อกำหนดสิทธิ์ที่บอทจะใช้
intents = nextcord.Intents.default()
intents.message_content = True

# สร้างออบเจ็กต์บอทด้วยคำสั่งที่ใช้ '!' เป็นพรีฟิกซ์
bot = commands.Bot(command_prefix='!', intents=intents)

# ตัวแปรสำหรับเก็บข้อมูลคีย์
keys_data = {}

def save_keys_data():
  #  """บันทึกข้อมูลคีย์ลงในไฟล์ JSON."""
    try:
        with open('keys_data.json', 'w') as file:
            json.dump(keys_data, file, indent=4)
    except IOError as e:
        print(f"Error saving keys data: {e}")

def save_keys_data():
   # """บันทึกข้อมูลคีย์ลงในไฟล์ JSON."""
    try:
        with open('keys_data.json', 'w') as file:
            json.dump(keys_data, file, indent=4)
        print("Keys data saved successfully.")
    except IOError as e:
        print(f"Error saving keys data: {e}")

def load_keys_data():
  #  """โหลดข้อมูลคีย์จากไฟล์ JSON."""
    global keys_data
    try:
        with open('keys_data.json', 'r') as file:
            keys_data = json.load(file)
        print("Keys data loaded successfully.")
    except FileNotFoundError:
        keys_data = {}
        print("No keys data found, initializing empty.")

def generate_key(length=10):
   # """สร้างคีย์สุ่มที่มีความยาวตามที่กำหนด."""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

class KeyClaimModal(Modal):
   # """Modal สำหรับให้ผู้ใช้กรอกคีย์เพื่อรับบทบาท."""
    def __init__(self):
        super().__init__("กรุณาใส่ Key", timeout=5 * 60)
        self.add_item(TextInput(label="Key", placeholder="Enter your key", custom_id="key_input"))

    async def callback(self, interaction: nextcord.Interaction):
        key = self.children[0].value
        user_id = str(interaction.user.id)

        # ตรวจสอบว่าคีย์มีอยู่ในข้อมูล
        if key in keys_data:
            # ตรวจสอบว่าคีย์ได้รับการใช้แล้วหรือยัง
            if keys_data[key].get('claimed'):
                if keys_data[key]['claimed'] == user_id:
                    await interaction.response.send_message("คุณใช้คึย์นี้ไปแล้ว.")
                else:
                    await interaction.response.send_message("คีย์ถูกใช้ไปแล้ว.")
                return

            # รับบทบาทตามคีย์ที่ใช้
            role_id = keys_data[key]['role_id']
            role = interaction.guild.get_role(int(role_id))
            if role:
                await interaction.user.add_roles(role)
                keys_data[key]['claimed'] = user_id
                save_keys_data()
                await interaction.response.send_message(f"คีย์ถูกต้อง! คุณได้รับบทบาท {role.name}.")
            else:
                await interaction.response.send_message("บทบาทไม่พบ.")
        else:
            await interaction.response.send_message("คีย์ไม่ถูกต้อง.")

class SetupView(View):
   # """View สำหรับแสดงปุ่มเพื่อเรียกร้องบทบาท."""
    @nextcord.ui.button(label="Claim Role", style=nextcord.ButtonStyle.primary, custom_id="claim_role")
    async def claim_role(self, button: Button, interaction: nextcord.Interaction):
        modal = KeyClaimModal()
        await interaction.response.send_modal(modal)

@bot.slash_command(name="setup", description="Setup the role claiming button.")
async def setup(interaction: nextcord.Interaction):
   # """คำสั่งสำหรับตั้งค่าปุ่มเรียกร้องบทบาท."""
    view = SetupView()
    
    embed = nextcord.Embed(
        title="กรอก Key เพื่อรับยศ",
        description="```รับยศเพื่อเห็นห้อง```",
        color=0x00ff00 
    )
    embed.set_image(url="https://c.tenor.com/J2qI_909o3wAAAAC/tenor.gif")
    embed.set_footer(text=f"Requested at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    await interaction.response.send_message(embed=embed, view=view)

@bot.slash_command(name="add", description="Add new keys and associate them with a role.")
async def add_key(interaction: nextcord.Interaction, key_count: int, role: nextcord.Role):
  #  """คำสั่งสำหรับเพิ่มคีย์ใหม่และเชื่อมโยงกับบทบาท."""
    if key_count <= 0:
        await interaction.response.send_message("The number of keys must be greater than 0.")
        return

    for _ in range(key_count):
        key = generate_key()
        while key in keys_data:  # ตรวจสอบให้แน่ใจว่าคีย์ไม่ซ้ำ
            key = generate_key()
        keys_data[key] = {
            'role_id': role.id,
            'claimed': None
        }

    save_keys_data()
    await interaction.response.send_message(f"{key_count} keys have been added with the role `{role.name}`.")

@bot.slash_command(name="check", description="Check the remaining keys.")
async def check_keys(interaction: nextcord.Interaction):
   # """คำสั่งสำหรับตรวจสอบคีย์ที่เหลืออยู่."""
    if keys_data:
        keys_list = [f"Key: {key}, Role ID: {data['role_id']}, Claimed: {'Yes' if data.get('claimed') else 'No'}"
                     for key, data in keys_data.items()]
        keys_info = "\n".join(keys_list)
    else:
        keys_info = "No keys available."

    await interaction.response.send_message(f"Remaining keys:\n```{keys_info}```")

@bot.event
async def on_ready():
  #  """ฟังก์ชันที่ทำงานเมื่อบอทพร้อมใช้งาน."""
    load_keys_data()
    print(f'Logged in as {bot.user.name}')

# เริ่มบอท

bot.run("")
