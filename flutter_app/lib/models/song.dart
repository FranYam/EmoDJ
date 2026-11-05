class Song {
  const Song({
    required this.title,
    required this.artist,
    required this.youtubeUrl,
  });

  final String title;
  final String artist;
  final String youtubeUrl;

  factory Song.fromJson(Map<String, dynamic> json) {
    return Song(
      title: json['title'] as String? ?? '',
      artist: json['artist'] as String? ?? '',
      youtubeUrl: json['youtube_url'] as String? ?? '',
    );
  }
}
