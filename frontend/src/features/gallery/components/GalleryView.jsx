import { useState, useEffect, useCallback } from 'react';
import { useGalleryStore } from '../../../stores/galleryStore';
import StoryReader from './StoryReader';
import './GalleryView.css';

/**
 * GalleryView — Full-screen bookshelf overlay for browsing completed storybooks.
 * Renders book cover cards on wooden shelf rows with shimmer loading and empty states.
 */
export default function GalleryView({ siblingPairId, onClose, isParentMode = false }) {
  const { storybooks, isLoading, error } = useGalleryStore();
  const [selectedBookId, setSelectedBookId] = useState(null);
  const [deletingIds, setDeletingIds] = useState(new Set());

  useEffect(() => {
    if (siblingPairId) {
      useGalleryStore.getState().fetchStorybooks(siblingPairId);
    }
  }, [siblingPairId]);

  const handleBookTap = useCallback((storybookId) => {
    setSelectedBookId(storybookId);
  }, []);

  const handleDelete = useCallback(async (e, storybookId) => {
    e.stopPropagation();
    const confirmed = window.confirm('Delete this adventure?');
    if (!confirmed) return;

    const pin = window.prompt('Enter parent PIN:');
    if (!pin) return;

    // Start fade-out animation
    setDeletingIds((prev) => new Set(prev).add(storybookId));

    const result = await useGalleryStore.getState().deleteStorybook(storybookId, pin);
    if (!result.success) {
      // Revert fade-out on failure
      setDeletingIds((prev) => {
        const next = new Set(prev);
        next.delete(storybookId);
        return next;
      });
      window.alert(result.error || 'Something went wrong — the book is still safe!');
    }
  }, []);

  // If a book is selected, show the StoryReader
  if (selectedBookId) {
    return (
      <StoryReader
        storybookId={selectedBookId}
        onClose={() => setSelectedBookId(null)}
      />
    );
  }

  return (
    <div className="gallery-overlay" role="dialog" aria-label="Story gallery">
      <div className="gallery-header">
        <h2 className="gallery-header__title">📚 Story Gallery</h2>
        <button
          className="gallery-header__close"
          onClick={onClose}
          aria-label="Close gallery"
        >
          ✕
        </button>
      </div>

      <div className="gallery-content" role="region" aria-label="Story gallery bookshelf">
        {isLoading && <ShimmerPlaceholders />}

        {!isLoading && error && (
          <div className="gallery-error">
            <p>Oops, the bookshelf is hiding! Try again.</p>
            <button
              className="gallery-error__retry"
              onClick={() => useGalleryStore.getState().fetchStorybooks(siblingPairId)}
            >
              Retry
            </button>
          </div>
        )}

        {!isLoading && !error && storybooks.length === 0 && (
          <div className="gallery-empty">
            <span className="gallery-empty__icon" aria-hidden="true">📖✨</span>
            <p className="gallery-empty__text">No adventures yet — start your first story!</p>
          </div>
        )}

        {!isLoading && !error && storybooks.length > 0 && (
          <div className="gallery-shelf">
            {storybooks.map((book) => (
              <button
                key={book.storybook_id}
                className={`gallery-book ${deletingIds.has(book.storybook_id) ? 'gallery-book--deleting' : ''}`}
                onClick={() => handleBookTap(book.storybook_id)}
                aria-label={`Open storybook: ${book.title}`}
              >
                <div className="gallery-book__cover">
                  {book.cover_image_url ? (
                    <img
                      src={
                        book.cover_image_url.startsWith('http')
                          ? book.cover_image_url
                          : `http://localhost:8000${book.cover_image_url}`
                      }
                      alt={book.title}
                      onError={(e) => {
                        e.target.style.display = 'none';
                        e.target.nextSibling.style.display = 'flex';
                      }}
                    />
                  ) : null}
                  <span
                    className="gallery-book__cover-fallback"
                    style={book.cover_image_url ? { display: 'none' } : {}}
                    aria-hidden="true"
                  >
                    📖
                  </span>
                </div>
                <span className="gallery-book__title">{book.title}</span>
                <span className="gallery-book__sparkle" aria-hidden="true">✨</span>

                {isParentMode && (
                  <button
                    className="gallery-book__delete"
                    onClick={(e) => handleDelete(e, book.storybook_id)}
                    aria-label={`Delete storybook: ${book.title}`}
                  >
                    🗑️
                  </button>
                )}
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

/** Shimmer skeleton placeholders during loading */
function ShimmerPlaceholders() {
  return (
    <div className="gallery-shelf" aria-busy="true" aria-label="Loading storybooks">
      {[0, 1, 2].map((i) => (
        <div key={i} className="gallery-shimmer" aria-hidden="true">
          <div className="gallery-shimmer__cover" />
          <div className="gallery-shimmer__title" />
        </div>
      ))}
    </div>
  );
}
