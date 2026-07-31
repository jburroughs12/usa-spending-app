import { useState, useCallback } from 'react';

const STORAGE_KEY = 'bookmarked-contracts';

function load() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

function save(bookmarks) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(bookmarks));
}

export default function useBookmarks() {
  const [bookmarks, setBookmarks] = useState(load);

  const toggle = useCallback((contract) => {
    setBookmarks(prev => {
      const id = contract['Award ID'];
      const exists = prev.some(b => b['Award ID'] === id);
      const next = exists
        ? prev.filter(b => b['Award ID'] !== id)
        : [...prev, { ...contract, bookmarked_at: new Date().toISOString() }];
      save(next);
      return next;
    });
  }, []);

  const isBookmarked = useCallback((awardId) => {
    return bookmarks.some(b => b['Award ID'] === awardId);
  }, [bookmarks]);

  const clear = useCallback(() => {
    save([]);
    setBookmarks([]);
  }, []);

  return { bookmarks, toggle, isBookmarked, clear };
}
