import os
import uuid
from datetime import datetime, date
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, jsonify, request, render_template, send_from_directory
from pymongo import MongoClient, ASCENDING, DESCENDING, ReturnDocument
from pymongo.errors import PyMongoError
from werkzeug.utils import secure_filename

load_dotenv()
BASE_DIR = Path(__file__).resolve().parent
UPLOAD_ROOT = BASE_DIR / "uploads"
VISIT_UPLOAD_DIR = UPLOAD_ROOT / "visit_proofs"
BILL_UPLOAD_DIR = UPLOAD_ROOT / "bill_proofs"
VISIT_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
BILL_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 20 * 1024 * 1024

MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "shepherd")
PORT = int(os.getenv("PORT", 3000))

if not MONGO_URI:
    raise RuntimeError("MONGO_URI is missing in .env")

mongo_client = MongoClient(MONGO_URI,serverSelectionTimeoutMS=10000)
db = mongo_client[MONGO_DB_NAME]

students = db.students
coordinators = db.coordinators
groups = db.shepherd_groups
members = db.group_members
plans = db.visit_plans
proofs = db.visit_proofs
bills = db.visit_bills
submissions = db.visit_submissions
counters = db.counters

def initialize_indexes():
    mongo_client.admin.command("ping")
    students.create_index(
        [("regno", ASCENDING)],
        unique=True
    )
    coordinators.create_index(
        [("faculty_id", ASCENDING)],
        unique=True
    )
    groups.create_index(
        [("group_id", ASCENDING)],
        unique=True
    )
    members.create_index(
        [("group_id", ASCENDING), ("regno", ASCENDING)],
        unique=True
    )
    members.create_index(
        [("regno", ASCENDING)]
    )
    plans.create_index(
        [("visit_id", ASCENDING)],
        unique=True
    )
    plans.create_index(
        [("group_id", ASCENDING), ("date_of_visit", DESCENDING)]
    )
    plans.create_index(
        [("faculty_id", ASCENDING), ("status", ASCENDING)]
    )
    proofs.create_index(
        [("visit_id", ASCENDING)]
    )
    bills.create_index(
        [("visit_id", ASCENDING)],
        unique=True
    )
    submissions.create_index(
        [("visit_id", ASCENDING)],
        unique=True
    )

    # --------------------------------------------------
# DEFAULT DATA
# --------------------------------------------------

def seed_default_data():

    created_at = datetime(2026, 10, 3, 14, 36, 5)

    # ----------------------------------------------
    # COORDINATOR
    # ----------------------------------------------

    coordinators.update_one(
        {"faculty_id": "20SAI51"},
        {
            "$setOnInsert": {
                "faculty_id": "20SAI51",
                "coordinator_name": "Lenin A",
                "contact_number": "9876543210",
                "email": "lenin@mail.sjctni.edu",
                "is_active": 1,
                "created_at": created_at,
                "updated_at": created_at
            }
        },
        upsert=True
    )

    # ----------------------------------------------
    # STUDENTS
    # ----------------------------------------------

    default_students = [

        {
            "regno": "25PAI818",
            "stud_name": "William James",
            "contact_number": "9876543210",
            "dept": "AI",
            "year": "II",
            "section": "A"
        },

        {
            "regno": "25PAI821",
            "stud_name": "Jeeva",
            "contact_number": "9876543211",
            "dept": "AI",
            "year": "II",
            "section": "A"
        },

        {
            "regno": "25PAI822",
            "stud_name": "Side Savari",
            "contact_number": "9876543212",
            "dept": "AI",
            "year": "II",
            "section": "A"
        }

    ]

    for student in default_students:

        students.update_one(
            {"regno": student["regno"]},
            {
                "$setOnInsert": {
                    **student,
                    "created_at": datetime(2026, 10, 3, 14, 41, 52),
                    "updated_at": datetime(2026, 10, 3, 14, 41, 52)
                }
            },
            upsert=True
        )

    # ----------------------------------------------
    # SHEPHERD GROUPS
    # ----------------------------------------------

    default_groups = [

        {
            "group_id": 1,
            "group_name": "Education",
            "village_name": "Pillaimanagar",
            "orientation_date": "2026-10-05",
            "one_day_visit": "2026-10-10",
            "camp_date": "2026-11-15",
            "total_hours": 70.00,
            "completed_hours": 20.00,
            "faculty_id": "20SAI51"
        },

        {
            "group_id": 2,
            "group_name": "Environment",
            "village_name": "Pillaimanagar",
            "orientation_date": "2026-10-06",
            "one_day_visit": "2026-10-11",
            "camp_date": "2026-11-16",
            "total_hours": 70.00,
            "completed_hours": 0.00,
            "faculty_id": "20SAI51"
        },

        {
            "group_id": 3,
            "group_name": "Health",
            "village_name": "Pillaimanagar",
            "orientation_date": "2026-10-07",
            "one_day_visit": "2026-10-12",
            "camp_date": "2026-11-17",
            "total_hours": 70.00,
            "completed_hours": 0.00,
            "faculty_id": "20SAI51"
        }

    ]

    for group in default_groups:

        groups.update_one(
            {"group_id": group["group_id"]},
            {
                "$setOnInsert": {
                    **group,
                    "created_at": created_at,
                    "updated_at": created_at
                }
            },
            upsert=True
        )

    # ----------------------------------------------
    # GROUP MEMBERS
    # ----------------------------------------------

    default_members = [

        {
            "group_id": 1,
            "regno": "25PAI818",
            "is_leader": 0
        },

        {
            "group_id": 2,
            "regno": "25PAI821",
            "is_leader": 1
        },

        {
            "group_id": 3,
            "regno": "25PAI822",
            "is_leader": 0
        }

    ]

    for member in default_members:

        members.update_one(
            {
                "group_id": member["group_id"],
                "regno": member["regno"]
            },
            {
                "$setOnInsert": {
                    **member,
                    "created_at": datetime(2026, 10, 3, 14, 43, 34),
                    "updated_at": datetime(2026, 10, 3, 14, 43, 34)
                }
            },
            upsert=True
        )

    print("Default Shepherd data inserted successfully!")


try:
    initialize_indexes()
    seed_default_data()

    print("MongoDB connected successfully!")
    print("Default Shepherd data is ready!")

except Exception as error:
    raise RuntimeError(
        f"MongoDB initialization failed: {error}"
    )


# --------------------------------------------------
# COMMON FUNCTIONS
# --------------------------------------------------

def response_error(message, code=400):
    return jsonify({
        "status": False,
        "message": message
    }), code


def get_form_value(name, default=""):
    value = request.form.get(name, default)

    if isinstance(value, str):
        return value.strip()

    return value


def next_id(sequence_name):

    result = counters.find_one_and_update(
        {"_id": sequence_name},
        {"$inc": {"sequence_value": 1}},
        upsert=True,
        return_document=ReturnDocument.AFTER
    )

    return result["sequence_value"]


def to_float(value, field_name):

    try:
        number = float(value)

        if number < 0:
            raise ValueError

        return number

    except (TypeError, ValueError):
        raise ValueError(f"Invalid {field_name}")


def json_safe(document):

    if isinstance(document, list):
        return [json_safe(item) for item in document]

    if isinstance(document, dict):
        return {
            key: json_safe(value)
            for key, value in document.items()
            if key != "_id"
        }

    if isinstance(document, (datetime, date)):
        return document.isoformat()

    return document


def find_member(regno):
    return members.find_one({"regno": regno})


def find_plan(visit_id):

    try:
        return plans.find_one({
            "visit_id": int(visit_id)
        })

    except (TypeError, ValueError):
        return None


def upload_pdf(file_storage, destination_dir, prefix, visit_id):

    if not file_storage or not file_storage.filename:
        raise ValueError("Both PDF files are required.")

    original_name = secure_filename(file_storage.filename)

    if Path(original_name).suffix.lower() != ".pdf":
        raise ValueError("Only PDF files are allowed.")

    file_storage.stream.seek(0)

    signature = file_storage.stream.read(5)

    file_storage.stream.seek(0)

    if signature != b"%PDF-":
        raise ValueError("The uploaded file is not a valid PDF.")

    filename = f"{prefix}_{visit_id}_{uuid.uuid4().hex}.pdf"

    full_path = destination_dir / filename

    file_storage.save(full_path)

    return str(
        full_path.relative_to(BASE_DIR)
    ).replace("\\", "/")


def delete_uploaded_file(relative_path):

    if not relative_path:
        return

    full_path = (BASE_DIR / relative_path).resolve()

    try:
        full_path.relative_to(UPLOAD_ROOT.resolve())

        if full_path.exists():
            full_path.unlink()

    except (ValueError, OSError):
        pass


# --------------------------------------------------
# HOME ROUTE
# --------------------------------------------------

@app.get("/")
def home():

    return jsonify({
        "status": True,
        "message": "Shepherd Flask API is running",
        "api": [
            "/api/requestweekendplan",
            "/api/approve_weekend_plan",
            "/api/get_request_status",
            "/api/submit_proof",
            "/api/verify_proof",
            "/api/payment_update",
            "/api/get_stud_dash"
        ],
        "staff_pages": [
            "/staff/approval",
            "/staff/verify",
            "/staff/payment"
        ]
    })


# --------------------------------------------------
# 2. REQUEST WEEKEND PLAN
# POST /api/requestweekendplan
# --------------------------------------------------

@app.post("/api/requestweekendplan")
def request_weekend_plan():

    regno = get_form_value("regno")
    date_of_visit = get_form_value("dateofvisit")
    objective = get_form_value("objective")
    plan_text = get_form_value("plan")

    if not all([
        regno,
        date_of_visit,
        objective,
        plan_text
    ]):
        return response_error("All fields are required")

    try:
        date.fromisoformat(date_of_visit)

    except ValueError:
        return response_error(
            "Invalid dateofvisit. Use YYYY-MM-DD"
        )

    member = find_member(regno)

    if not member:
        return response_error(
            "Student is not assigned to any group",
            404
        )

    if not member.get("is_leader", False):
        return response_error(
            "Only group leader can submit weekly plan",
            403
        )

    group = groups.find_one({
        "group_id": member["group_id"]
    })

    if not group:
        return response_error("Student group not found", 404)

    visit_id = next_id("visit_id")

    document = {
        "visit_id": visit_id,
        "group_id": member["group_id"],
        "faculty_id": group["faculty_id"],
        "date_of_visit": date_of_visit,
        "objective": objective,
        "plan": plan_text,
        "status": "pending",
        "remarks": None,
        "allocated_hours": 0.0,
        "created_by": regno,
        "approved_by": None,
        "approved_at": None,
        "verified_by": None,
        "verified_at": None,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }

    plans.insert_one(document)

    return jsonify({
        "status": True,
        "message": "Weekly plan submitted successfully",
        "visit_id": visit_id
    }), 201


# --------------------------------------------------
# 3. APPROVE / REJECT WEEKEND PLAN
# POST /api/approve_weekend_plan
# --------------------------------------------------

@app.post("/api/approve_weekend_plan")
def approve_weekend_plan():

    faculty_id = get_form_value("faculty_id")
    visit_id = get_form_value("visit_id")
    status = get_form_value("status").lower()
    remarks = get_form_value("remarks") or None

    if not faculty_id or not visit_id or not status:
        return response_error(
            "faculty_id, visit_id and status are required"
        )

    if status not in ("approved", "rejected"):
        return response_error("Invalid status")

    visit = find_plan(visit_id)

    if not visit:
        return response_error("Visit plan not found", 404)

    if visit.get("faculty_id") != faculty_id:
        return response_error(
            "You are not the coordinator for this plan",
            403
        )

    if visit.get("status") != "pending":
        return response_error(
            "This plan has already been processed"
        )

    result = plans.update_one(
        {
            "visit_id": visit["visit_id"],
            "status": "pending"
        },
        {
            "$set": {
                "status": status,
                "remarks": remarks,
                "approved_by": faculty_id,
                "approved_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
        }
    )

    if result.modified_count != 1:
        return response_error(
            "This plan has already been processed"
        )

    return jsonify({
        "status": True,
        "message": f"Plan {status} successfully"
    })


# --------------------------------------------------
# 4. GET REQUEST STATUS
# POST /api/get_request_status
# --------------------------------------------------

@app.post("/api/get_request_status")
def get_request_status():

    regno = get_form_value("regno")

    if not regno:
        return response_error("regno is required")

    member = find_member(regno)

    if not member:
        return response_error(
            "Student is not assigned to any group",
            404
        )

    visit_documents = list(
        plans.find({
            "group_id": member["group_id"]
        }).sort("date_of_visit", DESCENDING)
    )

    visits = []

    for visit in visit_documents:

        bill = bills.find_one({
            "visit_id": visit["visit_id"]
        }) or {}

        visits.append({
            "visit_id": visit.get("visit_id"),
            "group_id": visit.get("group_id"),
            "faculty_id": visit.get("faculty_id"),
            "date_of_visit": visit.get("date_of_visit"),
            "objective": visit.get("objective"),
            "plan": visit.get("plan"),
            "status": visit.get("status"),
            "remarks": visit.get("remarks"),
            "allocated_hours": visit.get("allocated_hours", 0),
            "bill_amount": bill.get("bill_amount"),
            "bill_status": bill.get("bill_status")
        })

    return jsonify({
        "status": True,
        "message": "Visit requests fetched successfully",
        "data": json_safe(visits)
    })


# --------------------------------------------------
# 5. SUBMIT VISIT PROOF AND BILL
# POST /api/submit_proof
# --------------------------------------------------

@app.post("/api/submit_proof")
def submit_proof():

    regno = get_form_value("regno")
    visit_id_raw = get_form_value("visit_id")
    proof_type = get_form_value("proof_type")
    bill_amount_raw = get_form_value("bill_amount")
    notes = get_form_value("notes") or None

    if not all([
        regno,
        visit_id_raw,
        proof_type,
        bill_amount_raw
    ]):
        return response_error("Required fields are missing")

    try:
        visit_id = int(visit_id_raw)
        bill_amount = to_float(
            bill_amount_raw,
            "bill amount"
        )

    except ValueError as error:
        return response_error(str(error))

    image_file = request.files.get("image_file")
    bill_file = request.files.get("bill_file")

    if not image_file or not bill_file:
        return response_error(
            "Visit proof and bill proof files are required"
        )

    member = find_member(regno)

    if not member:
        return response_error(
            "Student is not assigned to any group",
            404
        )

    if not member.get("is_leader", False):
        return response_error(
            "Only group leader can submit proof",
            403
        )

    visit = plans.find_one({
        "visit_id": visit_id,
        "group_id": member["group_id"]
    })

    if not visit:
        return response_error("Visit plan not found", 404)

    if visit.get("status") != "approved":
        return response_error("Visit plan is not approved")

    if bills.find_one({"visit_id": visit_id}):
        return response_error(
            "Proof and bill have already been submitted"
        )

    saved_paths = []

    try:

        image_path = upload_pdf(
            image_file,
            VISIT_UPLOAD_DIR,
            "visit",
            visit_id
        )

        saved_paths.append(image_path)

        bill_path = upload_pdf(
            bill_file,
            BILL_UPLOAD_DIR,
            "bill",
            visit_id
        )

        saved_paths.append(bill_path)

        proofs.insert_one({
            "proof_id": next_id("proof_id"),
            "visit_id": visit_id,
            "proof_type": proof_type,
            "image_path": image_path,
            "uploaded_by": regno,
            "uploaded_at": datetime.utcnow()
        })

        bills.insert_one({
            "bill_id": next_id("bill_id"),
            "visit_id": visit_id,
            "bill_proof_path": bill_path,
            "bill_amount": bill_amount,
            "bill_status": "pending",
            "transaction_id": None,
            "transaction_date": None,
            "verified_by": None,
            "verified_at": None,
            "remarks": None,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        })

        submissions.insert_one({
            "submission_id": next_id("submission_id"),
            "visit_id": visit_id,
            "submitted_by": regno,
            "submitted_at": datetime.utcnow(),
            "notes": notes
        })

    except Exception:

        for path in saved_paths:
            delete_uploaded_file(path)

        app.logger.exception("Proof submission failed")

        return response_error(
            "Failed to save proof submission",
            500
        )

    return jsonify({
        "status": True,
        "message": "Proof submitted successfully"
    }), 201


# --------------------------------------------------
# 6. VERIFY PROOF
# POST /api/verify_proof
# --------------------------------------------------

@app.post("/api/verify_proof")
def verify_proof():

    faculty_id = get_form_value("faculty_id")
    visit_id_raw = get_form_value("visit_id")
    bill_status = get_form_value("bill_status").lower()
    remarks = get_form_value("remarks") or None
    verified_by = get_form_value("verified_by")
    allocated_hours_raw = get_form_value("allocated_hours")

    if not all([
        faculty_id,
        visit_id_raw,
        bill_status,
        verified_by,
        allocated_hours_raw
    ]):
        return response_error("Required fields are missing")

    if bill_status not in ("approved", "rejected"):
        return response_error("Invalid bill status")

    if verified_by != faculty_id:
        return response_error("Invalid verified_by")

    try:
        visit_id = int(visit_id_raw)

        allocated_hours = to_float(
            allocated_hours_raw,
            "allocated hours"
        )

    except ValueError as error:
        return response_error(str(error))

    visit = find_plan(visit_id)

    if not visit:
        return response_error("Visit not found", 404)

    if visit.get("faculty_id") != faculty_id:
        return response_error(
            "You are not the coordinator for this visit",
            403
        )

    bill = bills.find_one({
        "visit_id": visit_id
    })

    if not bill:
        return response_error("Bill not found", 404)

    if bill.get("bill_status") != "pending":
        return response_error(
            "This bill has already been processed"
        )

    group = groups.find_one({
        "group_id": visit["group_id"]
    })

    if not group:
        return response_error("Group not found", 404)

    now = datetime.utcnow()

    new_visit_status = (
        "verified"
        if bill_status == "approved"
        else "rejected"
    )

    bill_result = bills.update_one(
        {
            "visit_id": visit_id,
            "bill_status": "pending"
        },
        {
            "$set": {
                "bill_status": bill_status,
                "remarks": remarks,
                "verified_by": verified_by,
                "verified_at": now,
                "updated_at": now
            }
        }
    )

    if bill_result.modified_count != 1:
        return response_error(
            "This bill has already been processed"
        )

    plans.update_one(
        {"visit_id": visit_id},
        {
            "$set": {
                "allocated_hours": (
                    allocated_hours
                    if bill_status == "approved"
                    else 0.0
                ),
                "verified_by": verified_by,
                "verified_at": now,
                "status": new_visit_status,
                "remarks": remarks,
                "updated_at": now
            }
        }
    )

    completed_hours = sum(
        float(item.get("allocated_hours", 0) or 0)
        for item in plans.find({
            "group_id": visit["group_id"],
            "status": "verified"
        })
    )

    groups.update_one(
        {"group_id": visit["group_id"]},
        {
            "$set": {
                "completed_hours": completed_hours,
                "updated_at": now
            }
        }
    )

    return jsonify({
        "status": True,
        "message": (
            "Proof verified successfully"
            if bill_status == "approved"
            else "Proof rejected successfully"
        ),
        "completed_hours": completed_hours
    })


# --------------------------------------------------
# 7. PAYMENT UPDATE
# POST /api/payment_update
# --------------------------------------------------

@app.post("/api/payment_update")
def payment_update():

    faculty_id = get_form_value("faculty_id")
    visit_id_raw = get_form_value("visit_id")
    transaction_id = get_form_value("transaction_id")
    transaction_date = get_form_value("transaction_date")

    if not all([
        faculty_id,
        visit_id_raw,
        transaction_id,
        transaction_date
    ]):
        return response_error("All fields are required")

    try:
        visit_id = int(visit_id_raw)
        date.fromisoformat(transaction_date)

    except ValueError:
        return response_error(
            "Invalid visit ID or transaction date"
        )

    visit = find_plan(visit_id)

    if not visit:
        return response_error("Visit not found", 404)

    if visit.get("faculty_id") != faculty_id:
        return response_error(
            "You are not the coordinator for this visit",
            403
        )

    bill = bills.find_one({
        "visit_id": visit_id
    })

    if not bill:
        return response_error("Bill not found", 404)

    if bill.get("bill_status") != "approved":
        return response_error(
            "Only approved bills can be marked as paid"
        )

    bills.update_one(
        {"visit_id": visit_id},
        {
            "$set": {
                "transaction_id": transaction_id,
                "transaction_date": transaction_date,
                "bill_status": "paid",
                "updated_at": datetime.utcnow()
            }
        }
    )

    return jsonify({
        "status": True,
        "visit_id": visit_id,
        "transaction_id": transaction_id,
        "transaction_date": transaction_date,
        "message": "Payment details updated successfully"
    })


# --------------------------------------------------
# 8. STUDENT DASHBOARD
# POST /api/get_stud_dash
# --------------------------------------------------

# --------------------------------------------------
# GET COMPLETE STUDENT DASHBOARD
# POST /api/get_student_dashboard
# --------------------------------------------------

@app.post("/api/get_stud_dash")
def get_student_dashboard():

    regno = get_form_value("regno")

    if not regno:
        return response_error("regno is required")

    # Student
    student = students.find_one({
        "regno": regno
    })

    if not student:
        return response_error("Student not found", 404)

    # Group membership
    member = members.find_one({
        "regno": regno
    })

    if not member:
        return response_error(
            "Student is not assigned to any group",
            404
        )

    # Group
    group = groups.find_one({
        "group_id": member["group_id"]
    })

    if not group:
        return response_error("Group not found", 404)

    # Coordinator
    coordinator = coordinators.find_one({
        "faculty_id": group.get("faculty_id")
    })

    if not coordinator:
        return response_error("Coordinator not found", 404)

    # Visit plans
    visit_documents = list(
        plans.find({
            "group_id": member["group_id"]
        }).sort("date_of_visit", ASCENDING)
    )

    dashboard_plans = []

    for visit in visit_documents:

        bill = bills.find_one({
            "visit_id": visit["visit_id"]
        })

        dashboard_plans.append({

            "visit_id": visit.get("visit_id"),
            "date_of_visit": visit.get("date_of_visit"),
            "objective": visit.get("objective"),
            "plan": visit.get("plan"),

            "status": visit.get("status"),
            "remarks": visit.get("remarks"),

            "allocated_hours": visit.get("allocated_hours", 0),

            "bill_amount": bill.get("bill_amount") if bill else None,
            "bill_status": bill.get("bill_status") if bill else None,

            "transaction_id": bill.get("transaction_id") if bill else None,
            "transaction_date": bill.get("transaction_date") if bill else None

        })

    # Final response
    return jsonify({

        "status": True,
        "message": "Student dashboard fetched successfully",

        "student": {

            "regno": student.get("regno"),
            "stud_name": student.get("stud_name"),
            "contact_number": student.get("contact_number"),
            "dept": student.get("dept"),
            "year": student.get("year"),
            "section": student.get("section"),

            "is_leader": member.get("is_leader", False)

        },

        "group": {

            "group_id": group.get("group_id"),
            "group_name": group.get("group_name"),
            "village_name": group.get("village_name"),

            "orientation_date": group.get("orientation_date"),
            "one_day_visit": group.get("one_day_visit"),
            "camp_date": group.get("camp_date"),

            "total_hours": group.get("total_hours", 0),
            "completed_hours": group.get("completed_hours", 0)

        },

        "coordinator": {

            "faculty_id": coordinator.get("faculty_id"),
            "coordinator_name": coordinator.get("coordinator_name"),
            "contact_number": coordinator.get("contact_number"),
            "email": coordinator.get("email")

        },

        "plans": dashboard_plans

    })

@app.get("/staff/approval")
def staff_approval_page():
    return render_template("staff_approval.html")

@app.get("/staff/verify")
def staff_verify_page():
    return render_template("staff_verify_proof.html")

@app.get("/staff/payment")
def staff_payment_page():
    return render_template("staff_payment_update.html")

@app.get("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(UPLOAD_ROOT,filename,as_attachment=False)

@app.errorhandler(413)
def request_entity_too_large(error):
    return response_error("Uploaded files are too large. Maximum request size is 20 MB.",413)

@app.errorhandler(PyMongoError)
def mongo_error(error):
    app.logger.exception("MongoDB operation failed")
    return response_error("Database operation failed",500)

if __name__ == "__main__":
    app.run(host="0.0.0.0",port=PORT,debug=os.getenv("FLASK_DEBUG") == "1")