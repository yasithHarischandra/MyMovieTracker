export function usePoster() {
  const getPosterUrl = (path, size = 'w500') => {
    // If we have an absolute URL returned from the backend directly, use it
    if (path && path.startsWith('http')) return path
    // The backend in this project returns the full w500 URL already in poster_path
    // So usually we can just return it. 
    return path || '/placeholder-poster.png'
  }

  // Linear gradients for missing posters, hashed by ID so they are consistent per show
  const getPlaceholderGradient = (id) => {
    const p = id ? (id % 5) : 0
    const gradients = [
      'from-slate-800 to-slate-900',
      'from-purple-900 to-slate-900',
      'from-blue-900 to-slate-900',
      'from-emerald-900 to-slate-900',
      'from-amber-900 to-slate-900'
    ]
    return gradients[p]
  }

  return { getPosterUrl, getPlaceholderGradient }
}
