"use strict";
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const html = fs.readFileSync("web/index.html", "utf8");
const script = html.split("<script>")[1].split("</script>")[0];
const nodes = new Map();
function node(id) {
  if (!nodes.has(id)) {
    nodes.set(id, {
      value: "", textContent: "", children: [], min: "", max: "",
      handlers: {},
      addEventListener(event, handler) { this.handlers[event] = handler; },
      replaceChildren(...children) { this.children = children; },
      append(...children) { this.children.push(...children); },
      reportValidity() { return true; }
    });
  }
  return nodes.get(id);
}
const document = { getElementById: node, createElement: () => ({className:"",textContent:""}) };
vm.runInNewContext(script, {document, Math, Number});
const click = (id, event) => node(id).handlers[event]({preventDefault() {}});
click("example", "click");
click("form", "submit");
assert.equal(node("result").children[0].textContent, "0.0668");
assert.match(node("result").children[1].textContent, /Below nonresponse/);
node("b7").value = "100";
click("form", "submit");
assert.match(node("result").children[1].textContent, /Nonresponse threshold/);
node("method").value = "inr";
click("method", "change");
assert.equal(node("coag").min, "0.5");
assert.equal(node("coag").max, "15");
console.log("Browser calculation smoke test passed");
