let items = document.querySelectorAll("ytd-playlist-video-renderer");
let data = Array.from(items).map(item => {
  let title = item.querySelector("#video-title").textContent.trim();
  let url = "https://www.youtube.com" + item.querySelector("#video-title").getAttribute("href");
  return [title, url];
});
let csvContent = "data:text/csv;charset=utf-8," + data.map(row => row.join(",")).join("\n");
let encodedUri = encodeURI(csvContent);
let link = document.createElement("a");
link.setAttribute("href", encodedUri);
link.setAttribute("download", "playlist_data.csv");
document.body.appendChild(link);
link.click();
