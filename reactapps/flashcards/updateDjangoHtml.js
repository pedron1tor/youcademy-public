const fs = require("fs-extra");
const path = require("path");

// Define paths
const buildDir = path.join(__dirname, "..", "..", "static", "react3");
const djangoHtmlFile = path.join(
  __dirname,
  "..",
  "..",
  "pages",
  "templates",
  "student",
  "flashcards.html"
);
const djangoCssFile = path.join(
  __dirname,
  "..",
  "..",
  "pages",
  "templates",
  "writing_layout.html"
);

// Read the built index.html file
const builtIndexHtml = path.join(buildDir, "index.html");
const newContent = fs.readFileSync(builtIndexHtml, "utf-8");

// Extract JavaScript and CSS file names
const jsFileMatch = newContent.match(
  /<script defer="defer" src="\/static\/js\/(main\.[a-z0-9]+\.js)"><\/script>/
);
const cssFileMatch = newContent.match(
  /<link href="\/static\/css\/(main\.[a-z0-9]+\.css)" rel="stylesheet">/
);

if (jsFileMatch && cssFileMatch) {
  const jsFile = jsFileMatch[1];
  const cssFile = cssFileMatch[1];

  // Read the Django HTML file
  let djangoHtmlContent = fs.readFileSync(djangoHtmlFile, "utf-8");
  let djangoCssContent = fs.readFileSync(djangoCssFile, "utf-8");

  // Replace the respective lines
  djangoHtmlContent = djangoHtmlContent.replace(
    /<script src="{% static 'react3\/static\/js\/main\.[a-z0-9]+\.js' %}"><\/script>/,
    `<script src="{% static 'react3/static/js/${jsFile}' %}"></script>`
  );

  djangoCssContent = djangoCssContent.replace(
    /react3\/static\/css\/main\.[a-z0-9]+\.css/,
    `react3/static/css/${cssFile}`
  );

  // Write the updated content back to the Django HTML file
  fs.writeFileSync(djangoHtmlFile, djangoHtmlContent, "utf-8");
  fs.writeFileSync(djangoCssFile, djangoCssContent, "utf-8");

  console.log(
    "Django HTML and CSS files have been updated with the new build content."
  );
} else {
  console.error(
    "Could not find the JavaScript or CSS file references in the built index.html."
  );
}
