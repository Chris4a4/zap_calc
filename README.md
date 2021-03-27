# TTCC Zap Calculator

Multithreaded TTCC Zap Calculator. Supports Python 2 and 3. Supports any number of cogs and toons.

## Usage
### Basic Usage

Enter cog levels or HPs, such as:

`14 10 17 11`

After running, the calculator will return every non-redundant squirt/zap/drop combo that will destroy the specified cogs. These are sorted from worst (at the top) to best (at the bottom). For example, running the above command will return:

```
Geyser 1         Geyser 1         Geyser 3         Lightning 3
Storm 1          Geyser 3         Lightning 3      Boulder 4
Storm 2          Storm 3          Taser 3          Lightning 1
Seltzer 3        Hose 2           TV 3             Lightning 1
Seltzer 1        Seltzer 4        Tesla 3          Tesla 1
Seltzer 2        Seltzer 4        Tesla 3          Tesla 1
```

Any of these combos will destroy all four cogs. Note that the order of zap gags used is important, and the calculator expects the gags to be used in **left to right order**. For example, `Seltzer 2        Seltzer 4        Tesla 3          Tesla 1` requires that the Tesla on the 3rd cog happens **first**, implying no cross.

### Specifying HPs

Cog HPs can be specified as an HP or a level. Any number above 20 is interpreted as a raw HP value, and anything 20 or below is interpreted as a level. You can also put an `e` after a level to specify an executive:

`10 240 13e`

### Specifying Pre-Soaked or Pre-Lured Cogs

Put `l` after a cog to indicate that it is lured. Put `pl` after to indicate that it is prestige lured. Put `s` after to indicate that it is already soaked. The order of these operators does not matter:

`240pls 16es 12el`

### Reverse Order

Starting a command with the lowercase letter `r` will reverse the cogs. This is often useful as cogs typically spawn in right to left order.

`r10 12 13e 6` is equivilant to `6 13e 12 10`

### Extra Options

Adding a `-` will indicate that extra options are wanted. These options include:

- Number of players: `10 12 13 6e - 3p` specifies only 3 toons. Can be used to indicate more than 4 toons.
- Number of zaps: `10 12 13 6e - 1z` will cause the calculator to only calculate and return solutions that use exactly 1 zap gag
- Number of squirts: `10 12 13 6e - 2s` same as above, but 2 squirt combos only
- Number of drops: `10 12 13 6e - 1d` same as above, but 1 drop combos

Any number of these can be combined.

## Limitations

At present, the calculator makes the following assumptions:

- All cogs must become soaked
- All toons have prestige squirt and zap
- No toons have prestige drop

If the calculator does something you didn't expect, it's probably the result of one of these assumptions.

## Other notes

Don't bother improving/optimizing this code. Python is a prototyping language and not intended for heavy-duty calculations like these. I will be rewriting this program in GPU-accelerated C++ to add more functionality (particularily sound) and optmizations when I can find the time.
