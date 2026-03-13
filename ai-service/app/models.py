from sqlalchemy import Column, Integer, String, Boolean, Numeric ,ForeignKey
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Category(Base):
    __tablename__ = "products_category"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    slug = Column(String)
    is_active = Column(Boolean)


class Brand(Base):
    __tablename__ = "products_brand"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    slug = Column(String)
    is_active = Column(Boolean)

class Product(Base):
    __tablename__ = "products_product"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    slug = Column(String)
    model_number = Column(String)

    category_id = Column(Integer, ForeignKey("products_category.id"))
    brand_id = Column(Integer, ForeignKey("products_brand.id"))

    price = Column(Numeric)
    stock_quantity = Column(Integer)

    is_active = Column(Boolean)
    is_deleted = Column(Boolean)

class CPUSpec(Base):
    __tablename__ = "products_cpuspec"

    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products_product.id"))

    socket = Column(String)
    cores = Column(Integer)
    threads = Column(Integer)

    base_clock = Column(Numeric)
    boost_clock = Column(Numeric)

    tdp = Column(Integer)

    has_integrated_graphics = Column(Boolean)

    series = Column(String)

class GPUSpec(Base):
    __tablename__ = "products_gpuspec"

    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products_product.id"))

    memory_gb = Column(Integer)
    memory_type = Column(String)

    base_clock_mhz = Column(Integer)
    boost_clock_mhz = Column(Integer)

    length_mm = Column(Integer)
    tdp = Column(Integer)

    recommended_psu_watt = Column(Integer)

    gpu_chipset = Column(String)

class RAMSpec(Base):
    __tablename__ = "products_ramspec"

    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products_product.id"))

    ram_type = Column(String)
    capacity_gb = Column(Integer)
    frequency_mhz = Column(Integer)
    stick_count = Column(Integer)

class MotherboardSpec(Base):
    __tablename__ = "products_motherboardspec"

    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products_product.id"))

    socket = Column(String)
    chipset = Column(String)

    ram_type = Column(String)

    max_ram_gb = Column(Integer)
    ram_slots = Column(Integer)

    form_factor = Column(String)

class StorageSpec(Base):
    __tablename__ = "products_storagespec"

    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products_product.id"))

    storage_type = Column(String)
    interface = Column(String)

    capacity_gb = Column(Integer)

    read_speed = Column(Integer)
    write_speed = Column(Integer)

class PSUSpec(Base):
    __tablename__ = "products_psuspec"

    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products_product.id"))

    wattage = Column(Integer)

    modular_type = Column(String)

    efficiency_rating = Column(String)

class CaseSpec(Base):
    __tablename__ = "products_casespec"

    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products_product.id"))

    supported_form_factors = Column(String)

    max_gpu_length_mm = Column(Integer)

    max_cpu_cooler_height_mm = Column(Integer)

class CoolerSpec(Base):
    __tablename__ = "products_coolerspec"

    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products_product.id"))

    cooler_type = Column(String)

    supported_sockets = Column(String)

    cooler_height_mm = Column(Integer)

class CaseFanSpec(Base):
    __tablename__ = "products_casefanspec"

    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products_product.id"))

    fan_size = Column(String)
    rpm = Column(Integer)

    has_rgb = Column(Boolean)