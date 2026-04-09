import os

project_dir = r'c:\Users\User\Desktop\crm-repair-system'
print("🚀 Начинаем восстановление раздела 'Заявки'...")

# 0. Восстанавливаем папку bot/ если её нет
bot_dir = os.path.join(project_dir, 'bot')
if not os.path.exists(bot_dir):
    os.makedirs(bot_dir)
    with open(os.path.join(bot_dir, 'Dockerfile'), 'w', encoding='utf-8') as f:
        f.write("FROM python:3.10-slim\nWORKDIR /app\nCOPY requirements.txt .\nRUN pip install --no-cache-dir -r requirements.txt\nCOPY main.py .\nCMD [\"python\", \"main.py\"]")
    with open(os.path.join(bot_dir, 'requirements.txt'), 'w', encoding='utf-8') as f:
        f.write("aiogram>=3.0.0\nhttpx\n")
    print("✅ Папка bot/ создана")

# 1. Models
models_path = os.path.join(project_dir, 'backend', 'models.py')
with open(models_path, 'r', encoding='utf-8') as f:
    content = f.read()

if 'class WorkBatch' not in content:
    new_models = """
# ============================================================
# WORK BATCHES (Заявки на работы)
# ============================================================
class WorkBatch(Base):
    __tablename__ = "work_batches"
    id = Column(Integer, primary_key=True, index=True)
    object_id = Column(Integer, ForeignKey("objects.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, default="")
    status = Column(String, default="draft")
    scheduled_at = Column(String, nullable=True)
    sent_at = Column(String, nullable=True)
    notes = Column(Text, default="")
    created_at = Column(String, default="")
    object = relationship("Object", back_populates="work_batches")
    items = relationship("WorkBatchItem", back_populates="batch", cascade="all, delete-orphan")
    contractors = relationship("WorkBatchContractor", back_populates="batch", cascade="all, delete-orphan")

class WorkBatchItem(Base):
    __tablename__ = "work_batch_items"
    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(Integer, ForeignKey("work_batches.id", ondelete="CASCADE"), nullable=False)
    estimate_item_id = Column(Integer, ForeignKey("estimate_items.id", ondelete="SET NULL"), nullable=True)
    name = Column(String, nullable=False)
    unit = Column(String, default="")
    quantity = Column(Float, default=0)
    description = Column(Text, default="")
    batch = relationship("WorkBatch", back_populates="items")
    estimate_item = relationship("EstimateItem")

class WorkBatchContractor(Base):
    __tablename__ = "work_batch_contractors"
    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(Integer, ForeignKey("work_batches.id", ondelete="CASCADE"), nullable=False)
    contractor_id = Column(Integer, ForeignKey("contractors.id", ondelete="CASCADE"), nullable=False)
    status = Column(String, default="pending")
    sent_at = Column(String, nullable=True)
    responded_at = Column(String, nullable=True)
    response_message = Column(Text, default="")
    response_price = Column(Float, nullable=True)
    batch = relationship("WorkBatch", back_populates="contractors")
    contractor = relationship("Contractor")

class TelegramUser(Base):
    __tablename__ = "telegram_users"
    id = Column(Integer, primary_key=True, index=True)
    contractor_id = Column(Integer, ForeignKey("contractors.id", ondelete="CASCADE"), nullable=True)
    telegram_id = Column(String, nullable=False, unique=True)
    telegram_username = Column(String, default="")
    first_name = Column(String, default="")
    last_name = Column(String, default="")
    created_at = Column(String, default="")
    contractor = relationship("Contractor")

"""
    if 'class Material(Base):' in content:
        content = content.replace('class Material(Base):', new_models + 'class Material(Base):')
        content = content.replace(
            'acts = relationship("Act", back_populates="object", cascade="all, delete-orphan")',
            'acts = relationship("Act", back_populates="object", cascade="all, delete-orphan")\n    work_batches = relationship("WorkBatch", back_populates="object", cascade="all, delete-orphan")'
        )
        with open(models_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print("✅ models.py обновлен")
    else:
        print("❌ Ошибка в models.py")
else:
    print("⚠️ models.py уже содержит WorkBatch")

# 2. Schemas
schemas_path = os.path.join(project_dir, 'backend', 'schemas.py')
with open(schemas_path, 'r', encoding='utf-8') as f:
    content = f.read()

if 'class WorkBatchCreate' not in content:
    new_schemas = """
# ===== ЗАЯВКИ НА РАБОТЫ =====
class WorkBatchItemCreate(BaseModel):
    estimate_item_id: Optional[int] = None
    name: str
    unit: str = "шт"
    quantity: float = 1

class WorkBatchCreate(BaseModel):
    object_id: int
    name: Optional[str] = None
    scheduled_at: Optional[str] = None
    notes: Optional[str] = None
    items: List[WorkBatchItemCreate] = []
    contractor_ids: List[int] = []

class TelegramUserCreate(BaseModel):
    contractor_id: Optional[int] = None
    telegram_id: str
    telegram_username: Optional[str] = None
"""
    content += new_schemas
    with open(schemas_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("✅ schemas.py обновлен")
else:
    print("⚠️ schemas.py уже содержит WorkBatchCreate")

# 3. Main (API)
main_path = os.path.join(project_dir, 'backend', 'main.py')
with open(main_path, 'r', encoding='utf-8') as f:
    content = f.read()

if 'def create_work_batch' not in content:
    new_api = """
# =====================
# ЗАЯВКИ НА РАБОТЫ
# =====================

@app.post("/work-batches/")
async def create_work_batch(data: schemas.WorkBatchCreate, db: Session = Depends(database.get_db)):
    obj = db.query(models.Object).filter(models.Object.id == data.object_id).first()
    if not obj: raise HTTPException(404, "Объект не найден")
    batch = models.WorkBatch(
        object_id=data.object_id, 
        name=data.name or f"Заявка: {obj.name}", 
        status="scheduled" if data.scheduled_at else "draft", 
        scheduled_at=data.scheduled_at, 
        notes=data.notes or "", 
        created_at=now_str()
    )
    db.add(batch); db.flush()
    for it in data.items:
        db.add(models.WorkBatchItem(batch_id=batch.id, estimate_item_id=it.estimate_item_id, name=it.name, unit=it.unit, quantity=it.quantity))
    for cid in data.contractor_ids:
        db.add(models.WorkBatchContractor(batch_id=batch.id, contractor_id=cid, status="pending"))
    db.commit(); db.refresh(batch)
    return {"id": batch.id, "name": batch.name, "status": batch.status, "items_count": len(data.items), "contractors_count": len(data.contractor_ids)}

@app.get("/work-batches/")
async def list_work_batches(object_id: Optional[int] = None, status: Optional[str] = None, db: Session = Depends(database.get_db)):
    q = db.query(models.WorkBatch).options(
        joinedload(models.WorkBatch.object), 
        joinedload(models.WorkBatch.items), 
        joinedload(models.WorkBatch.contractors).joinedload(models.WorkBatchContractor.contractor)
    )
    if object_id: q = q.filter(models.WorkBatch.object_id == object_id)
    if status: q = q.filter(models.WorkBatch.status == status)
    result = []
    for b in q.order_by(models.WorkBatch.id.desc()).all():
        result.append({
            "id": b.id, "object_id": b.object_id, "object_name": b.object.name if b.object else "", 
            "name": b.name, "status": b.status, "scheduled_at": b.scheduled_at, "created_at": b.created_at, "notes": b.notes, 
            "items": [{"id": i.id, "name": i.name, "unit": i.unit, "quantity": i.quantity} for i in b.items], 
            "contractors": [{"id": c.id, "contractor_id": c.contractor_id, "contractor_name": c.contractor.name if c.contractor else "", "status": c.status} for c in b.contractors]
        })
    return result

@app.get("/work-batches/{batch_id}")
async def get_work_batch(batch_id: int, db: Session = Depends(database.get_db)):
    b = db.query(models.WorkBatch).options(
        joinedload(models.WorkBatch.object), 
        joinedload(models.WorkBatch.items), 
        joinedload(models.WorkBatch.contractors).joinedload(models.WorkBatchContractor.contractor)
    ).filter(models.WorkBatch.id == batch_id).first()
    if not b: raise HTTPException(404)
    return {"id": b.id, "object_id": b.object_id, "object_name": b.object.name if b.object else "", "name": b.name, "status": b.status, "scheduled_at": b.scheduled_at, "notes": b.notes, "created_at": b.created_at, "items": [{"id": i.id, "name": i.name, "unit": i.unit, "quantity": i.quantity} for i in b.items], "contractors": [{"id": c.id, "contractor_id": c.contractor_id, "contractor_name": c.contractor.name if c.contractor else "", "status": c.status} for c in b.contractors]}

@app.put("/work-batches/{batch_id}")
async def update_work_batch(batch_id: int, data: dict, db: Session = Depends(database.get_db)):
    b = db.query(models.WorkBatch).filter(models.WorkBatch.id == batch_id).first()
    if not b: raise HTTPException(404)
    if "status" in data: b.status = data["status"]
    db.commit()
    return {"id": b.id, "status": b.status}

@app.delete("/work-batches/{batch_id}")
async def delete_work_batch(batch_id: int, db: Session = Depends(database.get_db)):
    b = db.query(models.WorkBatch).filter(models.WorkBatch.id == batch_id).first()
    if not b: raise HTTPException(404)
    db.delete(b); db.commit()
    return {"ok": True}

@app.post("/telegram-users/")
async def create_telegram_user(data: schemas.TelegramUserCreate, db: Session = Depends(database.get_db)):
    u = models.TelegramUser(contractor_id=data.contractor_id, telegram_id=data.telegram_id, telegram_username=data.telegram_username or "", first_name=data.first_name or "", last_name=data.last_name or "", created_at=now_str())
    db.add(u); db.commit(); db.refresh(u)
    return {"id": u.id, "telegram_id": u.telegram_id}

@app.get("/telegram-users/")
async def list_telegram_users(contractor_id: Optional[int] = None, db: Session = Depends(database.get_db)):
    q = db.query(models.TelegramUser).options(joinedload(models.TelegramUser.contractor))
    if contractor_id: q = q.filter(models.TelegramUser.contractor_id == contractor_id)
    return [{"id": u.id, "contractor_id": u.contractor_id, "contractor_name": u.contractor.name if u.contractor else "", "telegram_id": u.telegram_id} for u in q.all()]

"""
    if '# =====================\n# ГЛАВНАЯ' in content:
        content = content.replace('# =====================\n# ГЛАВНАЯ', new_api + '# =====================\n# ГЛАВНАЯ')
        with open(main_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print("✅ main.py обновлен")
    else:
        print("❌ Ошибка в main.py")
else:
    print("⚠️ main.py уже содержит API заявок")

# 4. Frontend
html_path = os.path.join(project_dir, 'backend', 'frontend', 'index.html')
with open(html_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 4.1 Nav
if 'data-s="work-batches"' not in content:
    content = content.replace(
        '<button class="nav-btn" data-s="finance">💰 Финансы</button>',
        '<button class="nav-btn" data-s="work-batches">📋 Заявки</button>\n  <button class="nav-btn" data-s="finance">💰 Финансы</button>'
    )
    print("✅ Навигация обновлена")

# 4.2 Section
if 'id="work-batches" class="section"' not in content:
    section_html = """
<!-- WORK BATCHES -->
<div id="work-batches" class="section">
  <div class="card" style="margin-bottom:12px"><button class="btn" onclick="openWbModal()">+ Создать заявку</button></div>
  <div class="card"><div id="wbList"></div></div>
</div>
"""
    content = content.replace('<!-- FINANCE -->', section_html + '<!-- FINANCE -->')
    print("✅ Секция добавлена")

# 4.3 Modal
if 'id="wbModal"' not in content:
    modal_html = """
<!-- Work Batch Modal -->
<div class="modal" id="wbModal"><div class="modal-box" style="max-width:900px">
  <div class="modal-head"><h3>Создать заявку</h3><button class="close-btn" onclick="closeM('wbModal')">&times;</button></div>
  <div class="fr"><div class="fg"><label>Объект *</label><select id="wbObj"></select></div></div>
  <div class="fg"><label>Название</label><input id="wbName" placeholder="Авто"></div>
  <h3 style="margin:12px 0 8px;font-size:14px">📋 Работы:</h3>
  <div id="wbItems" style="max-height:200px;overflow-y:auto;margin-bottom:12px"><p style="color:var(--sec)">Выбери объект</p></div>
  <h3 style="margin:12px 0 8px;font-size:14px">👷 Подрядчики (несколько):</h3>
  <div id="wbConts" style="max-height:150px;overflow-y:auto;margin-bottom:12px"></div>
  <div class="fr"><div class="fg"><label>Время отправки</label><input type="datetime-local" id="wbTime"></div><div class="fg"><label>Заметки</label><textarea id="wbNotes" rows="2"></textarea></div></div>
  <div class="btn-group" style="margin-top:12px"><button class="btn" onclick="saveWb()">📤 Создать</button><button class="btn btn-outline" onclick="closeM('wbModal')">Отмена</button></div>
</div></div>
"""
    content = content.replace('<script>', modal_html + '<script>')
    print("✅ Модалка добавлена")

# 4.4 JS
if 'function openWbModal' not in content:
    js_code = """
async function loadWb(){
  const items = await api('/work-batches/');
  $('wbList').innerHTML = items.length ? `<table><thead><tr><th>Дата</th><th>Объект</th><th>Название</th><th>Работ</th><th>Подрядчиков</th><th>Статус</th><th></th></tr></thead><tbody>${items.map(b=>`<tr><td>${b.created_at}</td><td>${esc(b.object_name)}</td><td><b>${esc(b.name)}</b></td><td>${(b.items||[]).length}</td><td>${(b.contractors||[]).length}</td><td>${badge(b.status)}</td><td class="btn-group"><button class="btn btn-sm btn-red" onclick="delWb(${b.id})">×</button></td></tr>`).join('')}</tbody></table>` : '<div class="empty">Нет заявок</div>';
}
function openWbModal(){
  $('wbObj').innerHTML='<option value="">Объект</option>'+D.objects.map(o=>`<option value="${o.id}">${esc(o.name)}</option>`).join('');
  $('wbConts').innerHTML=D.contractors.map(c=>`<label class="checkbox-item"><input type="checkbox" value="${c.id}"><div class="item-info"><div class="item-name">${esc(c.name)}</div></div></label>`).join('');
  $('wbName').value='';$('wbNotes').value='';$('wbItems').innerHTML='<p style="color:var(--sec)">Выбери объект</p>';
  openM('wbModal');
}
async function loadWbItems(){
  const oid=$('wbObj').value;if(!oid)return;
  const obj=D.objects.find(o=>o.id===+oid);if(!obj)return;
  const all=[];(obj.estimates||[]).forEach(e=>(e.items||[]).forEach(i=>all.push(i)));
  $('wbItems').innerHTML=all.map(i=>`<label class="checkbox-item"><input type="checkbox" class="wb-chk" value="${i.id}" data-n="${esc(i.name)}" data-u="${esc(i.unit)}" data-q="${i.quantity}"><div class="item-info"><div class="item-name">${esc(i.name)}</div><div class="item-details">${esc(i.unit)} × ${i.quantity}</div></div></label>`).join('');
}
async function saveWb(){
  const oid=+$('wbObj').value;if(!oid){notify('Выбери объект',false);return;}
  const items=[];document.querySelectorAll('.wb-chk:checked').forEach(cb=>items.push({estimate_item_id:+cb.value,name:cb.dataset.n,unit:cb.dataset.u,quantity:+cb.dataset.q}));
  if(!items.length){notify('Выбери работы',false);return;}
  const cids=[];document.querySelectorAll('#wbConts input:checked').forEach(cb=>cids.push(+cb.value));
  if(!cids.length){notify('Выбери подрядчиков',false);return;}
  await api('/work-batches/','POST',{object_id:oid,name:$('wbName').value||undefined,scheduled_at:$('wbTime').value||null,notes:$('wbNotes').value,items,contractor_ids:cids});
  closeM('wbModal');notify('Заявка создана!');loadWb();
}
async function delWb(id){if(!confirm('Удалить?'))return;await api(`/work-batches/${id}`,'DELETE');notify('Удалено');loadWb();}
$('wbObj').addEventListener('change',loadWbItems);

"""
    content = content.replace('// INIT\n', js_code + '// INIT\n')
    print("✅ JS функции добавлены")

# 4.5 loadSection
if "s==='work-batches'" not in content:
    content = content.replace("else if(s==='finance')", "else if(s==='work-batches'){await loadAll();loadWb()} else if(s==='finance')")
    print("✅ loadSection обновлен")

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(content)
print("✅ index.html полностью восстановлен")

# 5. Bot
bot_main_path = os.path.join(bot_dir, 'main.py')
if os.path.exists(bot_main_path):
    with open(bot_main_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if 'def send_work_batch_to_contractors' not in content:
        # Простая вставка логики отправки
        bot_code = """
async def send_work_batch_to_contractors(batch_id: int, items: list, object_name: str, contractor_ids: list):
    import random, asyncio
    items_text = "\\n".join([f"• {item['name']}: {item['quantity']} {item['unit']}" for item in items])
    message_text = f"🏗 <b>Новая заявка на работы</b>\\n📍 Объект: {object_name}\\n📋 <b>Список работ:</b>\\n{items_text}\\nНажмите кнопку ниже, чтобы ответить:"
    for idx, cid in enumerate(contractor_ids):
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{CRM_API_URL}/telegram-users/?contractor_id={cid}")
                users = resp.json()
            if not users: continue
            tid = users[0]["telegram_id"]
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="✅ Взять", callback_data=f"accept_{batch_id}")],
                [InlineKeyboardButton(text="💰 Цена", callback_data=f"bid_{batch_id}")],
                [InlineKeyboardButton(text="❌ Отказ", callback_data=f"decline_{batch_id}")]
            ])
            await bot.send_message(chat_id=tid, text=message_text, parse_mode="HTML", reply_markup=keyboard)
            if idx < len(contractor_ids) - 1:
                await asyncio.sleep(random.uniform(2, 4))
        except Exception as e:
            logging.error(f"Error sending to {cid}: {e}")

@dp.callback_query(lambda c: c.data.startswith(("accept_", "bid_", "decline_")))
async def handle_contractor_response(callback: CallbackQuery):
    action, bid = callback.data.split("_", 1)
    if action == "accept":
        await callback.answer("Принято!")
        await callback.message.edit_text(f"{callback.message.text}\\n\\n✅ <b>Принято</b>")
    elif action == "decline":
        await callback.answer("Отказано")
        await callback.message.edit_text(f"{callback.message.text}\\n\\n❌ <b>Отказ</b>")
"""
        if 'async def main():' in content:
            content = content.replace('async def main():', bot_code + '\nasync def main():')
            with open(bot_main_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print("✅ bot/main.py обновлен")
    else:
        print("⚠️ bot/main.py уже содержит логику")
else:
    print("❌ bot/main.py не найден")

print("\n🎉 Восстановление завершено! Теперь выполни commit и push.")