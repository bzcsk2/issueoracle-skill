function readFile(path: string): void {
  fs.readFile(path, "utf8", (err, data) => {
    if (err) {
      console.error("Failed to read file:", err);
      return;
    }
    console.log(data);
  });
}
