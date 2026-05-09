from sqlalchemy.orm import Session
from .database import SessionLocal
from .models import Product, CPUSpec, GPUSpec, MotherboardSpec, Category, RAMSpec, PSUSpec, StorageSpec, CaseSpec, CoolerSpec, CaseFanSpec
from google import genai
import os
import time

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

def get_best_gpu_under_budget(budget: int, brand=None, model=None):
    db: Session = SessionLocal()
    query = (
        db.query(Product, GPUSpec)
        .join(GPUSpec, Product.id == GPUSpec.product_id)
        .filter(Product.price <= budget)
        .filter(Product.is_active == True)
    )
    if brand:
        query = query.filter(Product.name.ilike(f"%{brand}%"))
    if model:
        query = query.filter(Product.name.ilike(f"%{model}%"))
    query = query.order_by(Product.price.desc())
    results = query.limit(3).all()
    gpus = []
    for product, gpu in results:
        gpus.append({
            "id": product.id,
            "name": product.name,
            "price": float(product.price),
            "memory": gpu.memory_gb,
            "chipset": gpu.gpu_chipset,
            "tdp": gpu.tdp,
            "length_mm": gpu.length_mm,
            "recommended_psu_watt": gpu.recommended_psu_watt
        })
    db.close()
    return gpus

def get_best_cpu_under_budget(budget, brand=None, model=None):
    db = SessionLocal()
    query = (
        db.query(Product, CPUSpec)
        .join(CPUSpec, Product.id == CPUSpec.product_id)
        .filter(Product.price <= budget)
        .filter(Product.is_active == True)
    )
    if brand:
        query = query.filter(Product.name.ilike(f"%{brand}%"))
    if model:
        query = query.filter(Product.name.ilike(f"%{model}%"))
    query = query.order_by(Product.price.desc())
    result = query.first()
    db.close()
    if not result:
        return None
    product, cpu = result
    return {
        "id": product.id,
        "name": product.name,
        "price": float(product.price),
        "cores": cpu.cores,
        "socket": cpu.socket,
        "tdp": cpu.tdp
    }

def build_pc_with_requirements(data: dict):
    budget = data.get("budget")
    cpu_brand = data.get("cpu_brand")
    cpu_model = data.get("cpu_model")
    gpu_brand = data.get("gpu_brand")
    gpu_model = data.get("gpu_model")
    ram_size = data.get("ram")
    return build_pc(
        budget,
        cpu_brand=cpu_brand,
        cpu_model=cpu_model,
        gpu_brand=gpu_brand,
        gpu_model=gpu_model,
        ram_size=ram_size
    )


def build_pc(budget, cpu_brand=None, cpu_model=None, gpu_brand=None, gpu_model=None, ram_size=None):
    # Percentages that sum to 100%
    gpu_budget        = int(budget * 0.38)
    cpu_budget        = int(budget * 0.20)
    motherboard_budget= int(budget * 0.13)
    ram_budget        = int(budget * 0.07)
    psu_budget        = int(budget * 0.08)
    storage_budget    = int(budget * 0.07)
    case_budget       = int(budget * 0.05)
    cooler_budget     = int(budget * 0.02)
    # case_fans come from whatever is left

    gpu_list = get_best_gpu_under_budget(gpu_budget, brand=gpu_brand, model=gpu_model)
    gpu = gpu_list[0] if gpu_list else None
    cpu = get_best_cpu_under_budget(cpu_budget, brand=cpu_brand, model=cpu_model)

    motherboard = None
    ram = None
    psu = None
    psu_watt = None

    if not gpu or not cpu:
        return {
            "build": None,
            "ai_explanation": f"Sorry, we couldn't find compatible GPU and CPU within ₹{budget:,} budget. Please increase your budget or check our available products."
        }

    if cpu:
        motherboard = get_motherboard_for_cpu(cpu["socket"], motherboard_budget)

    if motherboard:
        ram = get_ram_for_motherboard(motherboard["ram_type"], ram_budget)
        if ram_size and ram and ram["capacity_gb"] < ram_size:
            ram = get_ram_by_size(motherboard["ram_type"], ram_size)

    if cpu and gpu:
        psu_watt = gpu.get("recommended_psu_watt") or calculate_psu(cpu["tdp"], gpu["tdp"])
        psu = get_psu_for_build(psu_watt, psu_budget) # <-- pass budget

    storage = get_storage_for_build(budget, storage_budget)  # <-- pass budget
    case = None
    cooler = None

    if motherboard and gpu:
        case = get_case_for_build(motherboard["form_factor"], gpu["length_mm"], case_budget)

    if case and cpu:
        cooler = get_cooler_for_build(cpu["socket"], case["max_cpu_cooler_height_mm"], cooler_budget)

    case_fans = get_case_fans_for_build()

    build = {
        "budget": budget,
        "gpu": gpu,
        "cpu": cpu,
        "motherboard": motherboard,
        "ram": ram,
        "psu": psu,
        "recommended_psu_watt": psu_watt,
        "storage": storage,
        "case": case,
        "cooler": cooler,
        "case_fans": case_fans
    }
    explanation = generate_build_explanation(build)
    return {"build": build, "ai_explanation": explanation}

def get_motherboard_for_cpu(cpu_socket, budget):
    db = SessionLocal()
    result = (
        db.query(Product, MotherboardSpec)
        .join(MotherboardSpec, Product.id == MotherboardSpec.product_id)
        .join(Category, Product.category_id == Category.id)
        .filter(Category.name == "Motherboard")
        .filter(MotherboardSpec.socket == cpu_socket)
        .filter(Product.price <= budget)
        .order_by(Product.price.desc())
        .first()
    )
    if not result:
        result = (
            db.query(Product, MotherboardSpec)
            .join(MotherboardSpec, Product.id == MotherboardSpec.product_id)
            .join(Category, Product.category_id == Category.id)
            .filter(Category.name == "Motherboard")
            .filter(MotherboardSpec.socket == cpu_socket)
            .filter(Product.is_active == True)
            .order_by(Product.price.asc())
            .first()
        )
    db.close()
    if not result:
        return None
    product, motherboard = result
    return {
        "id": product.id,
        "name": product.name,
        "price": float(product.price),
        "socket": motherboard.socket,
        "chipset": motherboard.chipset,
        "ram_type": motherboard.ram_type,
        "form_factor": motherboard.form_factor
    }

def get_ram_for_motherboard(ram_type, budget):
    db = SessionLocal()
    result = (
        db.query(Product, RAMSpec)
        .join(RAMSpec, Product.id == RAMSpec.product_id)
        .join(Category, Product.category_id == Category.id)
        .filter(Category.name == "RAM")
        .filter(RAMSpec.ram_type == ram_type)
        .filter(Product.price <= budget)
        .order_by(Product.price.desc())
        .first()
    )
    if not result:
        result = (
            db.query(Product, RAMSpec)
            .join(RAMSpec, Product.id == RAMSpec.product_id)
            .join(Category, Product.category_id == Category.id)
            .filter(Category.name == "RAM")
            .filter(RAMSpec.ram_type == ram_type)
            .filter(Product.is_active == True)
            .order_by(Product.price.asc())
            .first()
        )
    db.close()
    if not result:
        return None
    product, ram = result
    return {
        "id": product.id,
        "name": product.name,
        "price": float(product.price),
        "capacity_gb": ram.capacity_gb,
        "frequency_mhz": ram.frequency_mhz,
        "ram_type": ram.ram_type
    }

def get_ram_by_size(ram_type, required_gb):
    """Cheapest RAM that meets the user-requested capacity."""
    db = SessionLocal()
    result = (
        db.query(Product, RAMSpec)
        .join(RAMSpec, Product.id == RAMSpec.product_id)
        .join(Category, Product.category_id == Category.id)
        .filter(Category.name == "RAM")
        .filter(RAMSpec.ram_type == ram_type)
        .filter(RAMSpec.capacity_gb >= required_gb)
        .filter(Product.is_active == True)
        .order_by(Product.price.asc())  # cheapest that satisfies
        .first()
    )
    db.close()
    if not result:
        return None
    product, ram = result
    return {
        "id": product.id,
        "name": product.name,
        "price": float(product.price),
        "capacity_gb": ram.capacity_gb,
        "frequency_mhz": ram.frequency_mhz,
        "ram_type": ram.ram_type
    }

def calculate_psu(cpu_tdp, gpu_tdp):
    cpu_tdp = cpu_tdp or 65     # default if None in DB
    gpu_tdp = gpu_tdp or 150    # default if None in DB
    recommended = cpu_tdp + gpu_tdp + 120
    if recommended <= 450:
        return 450
    elif recommended <= 550:
        return 550
    elif recommended <= 650:
        return 650
    elif recommended <= 750:
        return 750
    else:
        return 850


def get_psu_for_build(required_watt, budget=None):
    db = SessionLocal()
    query = (
        db.query(Product, PSUSpec)
        .join(PSUSpec, Product.id == PSUSpec.product_id)
        .join(Category, Product.category_id == Category.id)
        .filter(Category.name == "PSU")
        .filter(PSUSpec.wattage >= required_watt)
    )
    if budget:
        query = query.filter(Product.price <= budget)
    result = query.order_by(PSUSpec.wattage.asc()).first()

    # fallback: ignore budget, still get correct wattage
    if not result:
        result = (
            db.query(Product, PSUSpec)
            .join(PSUSpec, Product.id == PSUSpec.product_id)
            .join(Category, Product.category_id == Category.id)
            .filter(Category.name == "PSU")
            .filter(PSUSpec.wattage >= required_watt)
            .filter(Product.is_active == True)
            .order_by(Product.price.asc())
            .first()
        )

    db.close()
    if not result:
        return None
    product, psu = result
    return {
        "id": product.id,
        "name": product.name,
        "price": float(product.price),
        "wattage": psu.wattage,
        "efficiency": psu.efficiency_rating
    }


def get_storage_for_build(total_budget, storage_budget=None):
    db = SessionLocal()
    if total_budget < 60000:
        capacity = 500
    elif total_budget < 120000:
        capacity = 1000
    else:
        capacity = 2000
    
    query = (
        db.query(Product, StorageSpec)
        .join(StorageSpec, Product.id == StorageSpec.product_id)
        .join(Category, Product.category_id == Category.id)
        .filter(Category.name == "Storage")
        .filter(StorageSpec.capacity_gb >= capacity)
    )
    if storage_budget:
        query = query.filter(Product.price <= storage_budget)
    
    result = query.order_by(StorageSpec.capacity_gb.asc()).first()

    # fallback: ignore capacity filter, just get cheapest within budget
    if result is None:
        query2 = (
            db.query(Product, StorageSpec)
            .join(StorageSpec, Product.id == StorageSpec.product_id)
            .join(Category, Product.category_id == Category.id)
            .filter(Category.name == "Storage")
        )
        if storage_budget:
            query2 = query2.filter(Product.price <= storage_budget)
        result = query2.order_by(Product.price.asc()).first()

    db.close()
    if result is None:
        return None
    product, storage = result
    return {
        "id": product.id,
        "name": product.name,
        "price": float(product.price),
        "capacity_gb": storage.capacity_gb,
        "type": storage.storage_type,
        "interface": storage.interface,
        "read_speed": storage.read_speed
    }

def get_case_for_build(form_factor, gpu_length, case_budget=0):
    # case_budget = int(budget * 0.1)
    db = SessionLocal()
    results = (
        db.query(Product, CaseSpec)
        .join(CaseSpec, Product.id == CaseSpec.product_id)
        .join(Category, Product.category_id == Category.id)
        .filter(Category.name == "Case")
        .filter(Product.price <= case_budget)
        .order_by(Product.price.desc())
        .all()
    )
    # fallback: ignore budget, find cheapest compatible case
    if not results:
        results = (
            db.query(Product, CaseSpec)
            .join(CaseSpec, Product.id == CaseSpec.product_id)
            .join(Category, Product.category_id == Category.id)
            .filter(Category.name == "Case")
            .order_by(Product.price.asc())
            .all()
        )

    db.close()
    for product, case in results:
        supported = [f.strip() for f in case.supported_form_factors.split(",")]
        if form_factor in supported and case.max_gpu_length_mm >= gpu_length:
            return {
                "id": product.id,
                "name": product.name,
                "price": float(product.price),
                "supported_form_factors": case.supported_form_factors,
                "max_gpu_length_mm": case.max_gpu_length_mm,
                "max_cpu_cooler_height_mm": case.max_cpu_cooler_height_mm
            }
    return None


def get_cooler_for_build(cpu_socket, case_max_height, budget=None):
    db = SessionLocal()
    query = (
        db.query(Product, CoolerSpec)
        .join(CoolerSpec, Product.id == CoolerSpec.product_id)
        .join(Category, Product.category_id == Category.id)
        .filter(Category.name == "Cooler")
    )
    if budget:
        query = query.filter(Product.price <= budget)  # ← apply before .all()
    
    results = query.all()  # ← then call .all()

    # fallback: ignore budget, find cheapest compatible cooler
    if not results:
        results = (
            db.query(Product, CoolerSpec)
            .join(CoolerSpec, Product.id == CoolerSpec.product_id)
            .join(Category, Product.category_id == Category.id)
            .filter(Category.name == "Cooler")
            .order_by(Product.price.asc())
            .all()
        )
    db.close()
    
    for product, cooler in results:
        supported = [s.strip() for s in cooler.supported_sockets.split(",")]
        if cpu_socket in supported and cooler.cooler_height_mm <= case_max_height:
            return {
                "id": product.id,
                "name": product.name,
                "price": float(product.price),
                "cooler_type": cooler.cooler_type,
                "height_mm": cooler.cooler_height_mm
            }
    return None

def get_case_fans_for_build():
    db = SessionLocal()
    result = (
        db.query(Product, CaseFanSpec)
        .join(CaseFanSpec, Product.id == CaseFanSpec.product_id)
        .join(Category, Product.category_id == Category.id)
        .filter(Category.name == "Case Fan")
        .filter(Product.is_active == True) 
        .order_by(Product.price.asc())
        .first()
    )
    db.close()
    if not result:
        return None
    product, fan = result
    return {
        "id": product.id,
        "name": product.name,
        "price": float(product.price),
        "fan_size": fan.fan_size,
        "rpm": fan.rpm,
        "rgb": fan.has_rgb
    }

def generate_build_explanation(build):
    prompt = f"""
You are a PC building expert.
Explain the following PC build in a simple way.

Build:
{build}

Explain:
- Why the CPU and GPU pair well
- Why the PSU is sufficient
- Why the motherboard and RAM are compatible
- Why the case and cooler fit

Give a short explanation (4-5 sentences).
"""
    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model="gemini-3.1-flash-lite-preview",
                contents=prompt
            )
            return response.text
        except Exception as e:
            if "429" in str(e) and attempt < 2:
                time.sleep(30)
                continue
            return "This is a well-balanced PC build with compatible components."