import asyncio
from sqlalchemy.future import select
from app.database import get_db
from app.models.category import Category
from app.models.category_amenity import CategoryAmenity
from app.models.space import ListingType

GROUPS = {
    "ESPAÇOS": [
        {"slug": "piscinas", "name": "Piscinas Privativas", "icon": "🏊", "listing_type": ListingType.SPACE, "desc": "Piscinas para lazer e eventos"},
        {"slug": "churrasqueiras", "name": "Churrasqueiras", "icon": "🍖", "listing_type": ListingType.SPACE, "desc": "Áreas gourmet para encontros"},
        {"slug": "chacaras", "name": "Chácaras e Sítios", "icon": "🌳", "listing_type": ListingType.SPACE, "desc": "Natureza e lazer ao ar livre"},
        {"slug": "rooftops", "name": "Rooftops", "icon": "🌆", "listing_type": ListingType.SPACE, "desc": "Terraços com vistas incríveis"},
        {"slug": "saloes-festas", "name": "Salões de Festas", "icon": "🎉", "listing_type": ListingType.SPACE, "desc": "Espaços amplos para eventos"},
        {"slug": "estudios-foto", "name": "Estúdios Fotográficos", "icon": "📸", "listing_type": ListingType.SPACE, "desc": "Espaços equipados para criação"},
        {"slug": "estudios-podcast", "name": "Estúdios de Podcast", "icon": "🎙️", "listing_type": ListingType.SPACE, "desc": "Gravação de áudio e vídeo"},
        {"slug": "salas-reuniao", "name": "Salas de Reunião", "icon": "💼", "listing_type": ListingType.SPACE, "desc": "Espaços corporativos"},
    ],
    "ESPORTES": [
        {"slug": "quadras-areia", "name": "Quadras de Areia", "icon": "🏖️", "listing_type": ListingType.SPACE, "desc": "Beach Tennis, Vôlei e Futevôlei"},
        {"slug": "quadras-tenis", "name": "Quadras de Tênis", "icon": "🎾", "listing_type": ListingType.SPACE, "desc": "Saibro ou piso duro"},
        {"slug": "campos-futebol", "name": "Campos de Futebol", "icon": "⚽", "listing_type": ListingType.SPACE, "desc": "Society, campo ou salão"},
        {"slug": "quadras-poliesportivas", "name": "Poliesportivas", "icon": "🏀", "listing_type": ListingType.SPACE, "desc": "Basquete, futsal e vôlei"},
    ],
    "NÁUTICO": [
        {"slug": "lanchas", "name": "Lanchas", "icon": "🛥️", "listing_type": ListingType.VEHICLE, "desc": "Passeios e festas na água"},
        {"slug": "jet-skis", "name": "Jet Skis", "icon": "🌊", "listing_type": ListingType.VEHICLE, "desc": "Aventura e adrenalina"},
        {"slug": "veleiros", "name": "Veleiros", "icon": "⛵", "listing_type": ListingType.VEHICLE, "desc": "Tranquilidade e vento"},
    ],
    "VEÍCULOS": [
        {"slug": "motorhomes", "name": "Motorhomes", "icon": "🚐", "listing_type": ListingType.VEHICLE, "desc": "Viagens e acampamentos"},
        {"slug": "carros-classicos", "name": "Carros Clássicos", "icon": "🚘", "listing_type": ListingType.VEHICLE, "desc": "Para casamentos e ensaios"},
    ],
    "SERVIÇOS": [
        {"slug": "dj", "name": "DJs", "icon": "🎧", "listing_type": ListingType.SERVICE, "desc": "Animação para sua festa"},
        {"slug": "fotografos", "name": "Fotógrafos", "icon": "📷", "listing_type": ListingType.SERVICE, "desc": "Registre os melhores momentos"},
        {"slug": "buffet", "name": "Buffet e Catering", "icon": "🍽️", "listing_type": ListingType.SERVICE, "desc": "Comida boa para seus convidados"},
        {"slug": "bartenders", "name": "Bartenders", "icon": "🍸", "listing_type": ListingType.SERVICE, "desc": "Drinks e coquetéis"},
        {"slug": "churrasqueiros", "name": "Churrasqueiros", "icon": "🥩", "listing_type": ListingType.SERVICE, "desc": "Especialistas em carne"},
        {"slug": "limpeza", "name": "Limpeza Pré/Pós", "icon": "🧹", "listing_type": ListingType.SERVICE, "desc": "Deixe o espaço impecável"},
        {"slug": "seguranca", "name": "Segurança", "icon": "👮", "listing_type": ListingType.SERVICE, "desc": "Tranquilidade para o evento"},
        {"slug": "recreacao", "name": "Recreação Infantil", "icon": "🤹", "listing_type": ListingType.SERVICE, "desc": "Diversão para as crianças"},
    ],
    "EQUIPAMENTOS": [
        {"slug": "som-iluminacao", "name": "Som e Iluminação", "icon": "🔊", "listing_type": ListingType.EQUIPMENT, "desc": "Equipamentos para festa"},
        {"slug": "brinquedos-inflaveis", "name": "Brinquedos Infláveis", "icon": "🏰", "listing_type": ListingType.EQUIPMENT, "desc": "Pula-pula, tobogã"},
        {"slug": "mesas-cadeiras", "name": "Mesas e Cadeiras", "icon": "🪑", "listing_type": ListingType.EQUIPMENT, "desc": "Mobiliário para eventos"},
        {"slug": "tendas-gazebos", "name": "Tendas e Gazebos", "icon": "⛺", "listing_type": ListingType.EQUIPMENT, "desc": "Proteção contra sol e chuva"},
        {"slug": "equipamentos-foto", "name": "Equipamentos Fotográficos", "icon": "🎥", "listing_type": ListingType.EQUIPMENT, "desc": "Câmeras, luzes e lentes"},
        {"slug": "equipamentos-esporte", "name": "Equipamentos Esportivos", "icon": "🏓", "listing_type": ListingType.EQUIPMENT, "desc": "Raquetes, bolas, redes"},
    ]
}

AMENITIES = {
    ListingType.SPACE: [
        {"name": "Wi-Fi", "icon": "wifi"},
        {"name": "Ar Condicionado", "icon": "ac_unit"},
        {"name": "Churrasqueira", "icon": "outdoor_grill"},
        {"name": "Piscina", "icon": "pool"},
        {"name": "Banheiro", "icon": "wc"},
        {"name": "Estacionamento", "icon": "local_parking"},
        {"name": "Geladeira", "icon": "kitchen"},
        {"name": "Som Bluetooth", "icon": "speaker"},
        {"name": "TV", "icon": "tv"},
    ],
    ListingType.VEHICLE: [
        {"name": "Cabine", "icon": "bed"},
        {"name": "Banheiro", "icon": "wc"},
        {"name": "Churrasqueira", "icon": "outdoor_grill"},
        {"name": "Som Bluetooth", "icon": "speaker"},
        {"name": "Coletes Salva-vidas", "icon": "lifebuoy"},
        {"name": "Boias", "icon": "sports_baseball"},
    ]
}

async def seed():
    async for db in get_db():
        try:
            order_idx = 0
            for group, categories in GROUPS.items():
                for cat_data in categories:
                    stmt = select(Category).where(Category.slug == cat_data['slug'])
                    result = await db.execute(stmt)
                    existing = result.scalar_one_or_none()
                    
                    if existing:
                        print(f"Updating '{cat_data['name']}'...")
                        existing.parent_group = group
                        existing.listing_type = cat_data["listing_type"]
                        existing.description = cat_data["desc"]
                        existing.icon = cat_data["icon"]
                        existing.order = order_idx
                    else:
                        print(f"Adding '{cat_data['name']}'...")
                        new_cat = Category(
                            slug=cat_data['slug'],
                            name=cat_data['name'],
                            icon=cat_data['icon'],
                            parent_group=group,
                            description=cat_data['desc'],
                            listing_type=cat_data['listing_type'],
                            is_active=True,
                            order=order_idx
                        )
                        db.add(new_cat)
                        existing = new_cat
                        await db.flush()

                    # Handle amenities
                    await db.execute(CategoryAmenity.__table__.delete().where(CategoryAmenity.category_id == existing.id))
                    
                    if existing.listing_type in AMENITIES:
                        for idx, am in enumerate(AMENITIES[existing.listing_type]):
                            db.add(CategoryAmenity(
                                category_id=existing.id,
                                name=am["name"],
                                icon=am["icon"],
                                order=idx
                            ))
                    
                    order_idx += 1
                    
            await db.commit()
            print("Successfully seeded all categories and amenities.")
        except Exception as e:
            await db.rollback()
            print(f"Error: {e}")
            raise
        finally:
            break

if __name__ == "__main__":
    asyncio.run(seed())
