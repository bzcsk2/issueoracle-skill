function readFile(path: string): void {
  fs.readFile(path, "utf8", (err, data) => {
    if (err) throw err;
    console.log(data);
  });
}
