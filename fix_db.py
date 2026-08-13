from app import create_app, db

app = create_app()
with app.app_context():
    try:
        db.session.execute(db.text("ALTER TABLE supplier_payment ADD COLUMN type VARCHAR(20)"))
        db.session.execute(db.text("UPDATE supplier_payment SET type = 'Payment' WHERE type IS NULL"))
        
        db.session.commit()
        print("✅ SUCCESS: Database updated! Column 'type' has been added successfully.")
        
    except Exception as e:
        if "already exists" in str(e).lower():
            print("✅ SUCCESS: Column 'type' already exists. Everything is fine!")
        else:
            print(f"❌ ERROR: {e}")