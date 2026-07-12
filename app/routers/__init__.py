from app.routers import auth, users, spaces, bookings, reviews, payments, chat, upload, health, favorites, notifications, reports, promotions, categories

def include_routers(app):
    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(users.router)
    app.include_router(spaces.router)
    app.include_router(spaces.host_router)
    app.include_router(bookings.router)
    app.include_router(reviews.router)
    app.include_router(payments.router)
    app.include_router(chat.router)
    app.include_router(upload.router)
    app.include_router(favorites.router)
    app.include_router(notifications.router)
    app.include_router(reports.router)
    app.include_router(promotions.router)
    app.include_router(categories.router)

