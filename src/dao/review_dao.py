"""评分评论数据访问层"""
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from ..db.models import BookReview


def create_review(db: Session, book_id: int, user_id: int, rating: int, comment: Optional[str] = None) -> BookReview:
    r = BookReview(book_id=book_id, user_id=user_id, rating=rating, comment=comment)
    db.add(r); db.commit(); db.refresh(r)
    return r


def get_user_review(db: Session, book_id: int, user_id: int) -> Optional[BookReview]:
    return db.query(BookReview).filter(BookReview.book_id == book_id, BookReview.user_id == user_id).first()


def get_book_reviews(db: Session, book_id: int, page: int = 1, size: int = 10) -> tuple:
    q = db.query(BookReview).filter(BookReview.book_id == book_id)
    total = q.count()
    items = q.order_by(desc(BookReview.id)).offset((page - 1) * size).limit(size).all()
    return items, total


def get_book_avg_rating(db: Session, book_id: int) -> Optional[float]:
    row = db.query(func.avg(BookReview.rating), func.count(BookReview.id)).filter(BookReview.book_id == book_id).first()
    return {"avg": float(row[0]) if row[0] else 0.0, "count": row[1]}


def delete_review(db: Session, review_id: int) -> bool:
    r = db.query(BookReview).filter(BookReview.id == review_id).first()
    if not r: return False
    db.delete(r); db.commit()
    return True


def list_all_reviews(db: Session, page: int = 1, size: int = 10) -> tuple:
    q = db.query(BookReview)
    total = q.count()
    items = q.order_by(desc(BookReview.id)).offset((page - 1) * size).limit(size).all()
    return items, total
