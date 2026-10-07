import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import configure_mappers
from sqlmodel import Session, select

from app.models.knowledge_base import KnowledgeBase
from app.models.link import Link
from app.models.particule import Particule
from app.models.particule_link import ParticuleLink
from app.models.particule_tag import ParticuleTag
from app.models.source import Source
from app.models.tag import Tag


def make_particule(knowledge_base: KnowledgeBase, permalink: str = "note-1", **kwargs) -> Particule:
    return Particule(
        title="A note",
        permalink=permalink,
        content="Some content",
        origins="book",
        knowledge_base=knowledge_base,
        **kwargs,
    )


def test_mappers_configure():
    # Fails on wrong back_populates, missing foreign keys, unknown classes...
    configure_mappers()


def test_create_particule_with_relationships(session: Session):
    knowledge_base = KnowledgeBase()
    source = Source(authors="Niklas Luhmann", year=1981, edition="1st", publisher="Suhrkamp")
    particule = make_particule(
        knowledge_base,
        source=source,
        links=[Link(link="https://example.com")],
        tags=[Tag(tag="zettelkasten")],
    )
    session.add(particule)
    session.commit()
    session.refresh(particule)

    assert particule.id is not None
    assert particule.source_id == source.id
    assert particule.knowledge_base_id == knowledge_base.id
    assert [link.link for link in particule.links] == ["https://example.com"]
    assert [tag.tag for tag in particule.tags] == ["zettelkasten"]

    # back_populates: the other side sees the particule too
    assert source.particules == [particule]
    assert knowledge_base.particules == [particule]
    assert particule.links[0].particules == [particule]
    assert particule.tags[0].particules == [particule]


def test_particule_without_source(session: Session):
    particule = make_particule(KnowledgeBase())
    session.add(particule)
    session.commit()

    assert particule.source is None


def test_tag_shared_between_particules(session: Session):
    knowledge_base = KnowledgeBase()
    tag = Tag(tag="memory")
    first = make_particule(knowledge_base, permalink="note-1", tags=[tag])
    second = make_particule(knowledge_base, permalink="note-2", tags=[tag])
    session.add_all([first, second])
    session.commit()
    session.refresh(tag)

    assert {p.permalink for p in tag.particules} == {"note-1", "note-2"}
    assert len(session.exec(select(Tag)).all()) == 1


def test_permalink_is_unique(session: Session):
    knowledge_base = KnowledgeBase()
    session.add(make_particule(knowledge_base, permalink="same"))
    session.add(make_particule(knowledge_base, permalink="same"))

    with pytest.raises(IntegrityError):
        session.commit()


def test_knowledge_base_is_required(session: Session):
    particule = Particule(title="A note", permalink="note-1", content="c", origins="o")
    session.add(particule)

    with pytest.raises(IntegrityError):
        session.commit()


def test_delete_source_keeps_particules(session: Session):
    source = Source(authors="a", year=2020, edition="1", publisher="p")
    particule = make_particule(KnowledgeBase(), source=source)
    session.add(particule)
    session.commit()

    session.delete(source)
    session.commit()
    session.refresh(particule)

    assert session.get(Particule, particule.id) is not None
    assert particule.source_id is None


def test_delete_particule_removes_link_rows_only(session: Session):
    link = Link(link="https://example.com")
    tag = Tag(tag="zettelkasten")
    particule = make_particule(KnowledgeBase(), links=[link], tags=[tag])
    session.add(particule)
    session.commit()

    session.delete(particule)
    session.commit()

    assert session.exec(select(ParticuleLink)).all() == []
    assert session.exec(select(ParticuleTag)).all() == []
    # Links and tags themselves stay, they may be used by other particules
    assert session.get(Link, link.id) is not None
    assert session.get(Tag, tag.id) is not None
